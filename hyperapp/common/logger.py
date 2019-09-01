import asyncio
from collections import namedtuple
from contextlib import contextmanager
from enum import Enum
from functools import wraps
from pathlib import Path
import inspect
import logging

import contextvars

from .htypes import meta_ref_t, t_ref, t_field_meta, t_record_meta, ref_t, capsule_t
from .htypes.deduce_value_type import DeduceTypeError, deduce_value_type
from .ref import ref_repr

_log = logging.getLogger(__name__)


class RecordKind(Enum):
    LEAF = 1
    ENTER = 2
    EXIT = 3


class LogRecord(namedtuple('_LogRecordBase', 'kind context module_ref name params')):

    def __new__(cls, kind, context, module_ref=None, name=None, params=None):
        return super().__new__(cls, kind, context.copy(), module_ref, name, params)

    def clone_with(self, kind, context):
        return LogRecord(kind, context, self.module_ref, self.name, self.params)


def _adjust_fn_params(params):

    def adjust_value(value):
        if isinstance(value, Path):
            return str(value)
        return value

    return {name: adjust_value(value) for name, value in params.items()
            if name != 'self' and value is not None}


class _LogFnAdapter:

    def __init__(self):
        pass

    def __getattr__(self, name):
        return _LoggerAdapter(name)

    def __call__(self, *args, **kw):
        assert len(args) == 1 and not kw and callable(args[0])
        fn = args[0]
        sig = inspect.signature(fn)
        default_params = {
            name: parameter.default
            for name, parameter in sig.parameters.items()
            if parameter.default is not inspect.Parameter.empty
            }
        param_names = list(sig.parameters)

        @wraps(fn)
        def wrapper(*args, **kw):
            name = fn.__qualname__
            args_params = {
                param_names[idx]: arg
                for idx, arg in enumerate(args)
                }
            fn_params = _adjust_fn_params({**default_params, **args_params, **kw})
            logger = _Logger.get_instance()
            if logger:
                module_ref = logger.make_module_ref(inspect.stack()[1].frame.f_globals)
                params_t = logger.get_params_t(module_ref, name, fn_params)
                params = params_t(**fn_params)
                logger.enter_context(module_ref, name, params)
            try:
                return fn(*args, **kw)
            finally:
                if logger:
                    logger.exit_context()

        return wrapper


log = _LogFnAdapter()


class _LoggerAdapter:

    def __init__(self, record_name):
        self._record_name = record_name

    def __call__(self, **kw):
        logger = _Logger.get_instance()
        if logger:
            module_ref = logger.make_module_ref(inspect.stack()[1].frame.f_globals)
            params_t = logger.get_params_t(module_ref, self._record_name, kw)
            params = params_t(**kw)
            logger.add_entry(module_ref, self._record_name, params)
        return _ContextAdapter()


class _ContextAdapter:

    def __init__(self):
        pass

    def __enter__(self):
        logger = _Logger.get_instance()
        if logger:
            logger.push_context()

    def __exit__(self, exc, value, tb):
        logger = _Logger.get_instance()
        if logger:
            logger.exit_context()


@contextmanager
def with_flag_set(flag):
    flag.set(True)
    try:
        yield
    finally:
        flag.set(False)


class _Logger:

    instance = None
    _inside_storage = contextvars.ContextVar('logger_context', default=False)
    _context_var = contextvars.ContextVar('logger_context', default=None)
    _pending_record = contextvars.ContextVar('logger_pending_record', default=None)

    @classmethod
    def get_instance(cls):
        if cls._inside_storage.get():
            return None
        else:
            return cls.instance

    def __init__(self, type_resolver, ref_registry, module_ref_resolver, storage):
        self._type_resolver = type_resolver
        self._ref_registry = ref_registry
        self._module_ref_resolver = module_ref_resolver
        self._storage = storage
        self._context_counter = 0
        self._params_t_cache = {}  # (module_ref, name) -> params_t

    @with_flag_set(_inside_storage)
    def make_module_ref(self, module_vars):
        return self._module_ref_resolver.get_module_ref(module_vars)

    @with_flag_set(_inside_storage)
    def get_params_t(self, module_ref, entry_name, params):
        key = (module_ref, entry_name)
        params_t = self._params_t_cache.get(key)
        if params_t is not None:
            return params_t
        fields = []
        for name, value in params.items():
            try:
                t = deduce_value_type(value)
            except DeduceTypeError:
                raise RuntimeError("Undeducable parameter {}.{}".format(entry_name, name))
            type_ref = self._type_resolver.reverse_resolve(t)
            fields.append(t_field_meta(name, t_ref(type_ref)))
        type_name = entry_name.replace('.', '_')
        type_rec = meta_ref_t(type_name, t_record_meta(fields))
        params_t = self._type_resolver.register_type(self._ref_registry, type_rec).t
        self._params_t_cache[key] = params_t
        return params_t

    @with_flag_set(_inside_storage)
    def add_entry(self, module_ref, name, params):
        self._log('add_entry: %s %r %r', ref_repr(module_ref), name, params)
        self._flush()
        self._pending_record.set(
            LogRecord(RecordKind.LEAF, self._context, module_ref, name, params))

    @with_flag_set(_inside_storage)
    def enter_context(self, module_ref, name, params):
        self._log('enter_context: %s %r %r', ref_repr(module_ref), name, params)
        self._flush()
        self._context_counter += 1
        self._context_append(self._context_counter)
        self._store_record(
            LogRecord(RecordKind.ENTER, self._context, module_ref, name, params))

    @with_flag_set(_inside_storage)
    def push_context(self):
        self._log('push_context')
        record = self._pending_record.get()
        assert record
        self._pending_record.set(None)
        self._context_counter += 1
        self._context_append(self._context_counter)
        self._store_record(
            record.clone_with(RecordKind.ENTER, self._context))

    @with_flag_set(_inside_storage)
    def exit_context(self):
        self._log('exit_context')
        self._flush()
        assert self._context
        self._store_record(
            LogRecord(RecordKind.EXIT, self._context))
        self._context_pop()

    @with_flag_set(_inside_storage)
    def flush(self):
        self._flush()

    def init_asyncio_task_factory(self):
        loop = asyncio.get_event_loop()
        loop.set_task_factory(self._task_factory)

    def _task_factory(self, loop, coro):
        async def wrapper():
            await coro
            if _Logger.instance:
                _Logger.instance.flush()
        return asyncio.Task(wrapper(), loop=loop)

    def _flush(self):
        pending_record = self._pending_record.get()
        if pending_record:
            self._store_record(pending_record)
            self._pending_record.set(None)

    @property
    def _context(self):
        return self._context_var.get() or []

    def _context_append(self, value):
        context = self._context_var.get() or []
        self._context_var.set(context + [value])

    def _context_pop(self):
        context = self._context_var.get()
        assert context
        self._context_var.set(context[:-1])

    def _store_record(self, record):
        self._log('store record: %r', record, level=logging.INFO)
        self._storage.add_record(record)

    def _log(self, format, *args, level=logging.DEBUG):
        _log.log(level, '  logger (context=%r pending=%r) ' + format, self._context, self._pending_record.get(), *args)


def init_logger(type_resolver, ref_registry, module_ref_resolver, storage):
    _Logger.instance = logger = _Logger(type_resolver, ref_registry, module_ref_resolver, storage)
    return logger


def close_logger():
    logger = _Logger.instance
    _Logger.instance = None
    logger.flush()


def create_context_task(coro, log_context, **kw):
    async def wrapper():
        with log_context(**kw):
            await coro
        if _Logger.instance:
            _Logger.instance.flush()
    return asyncio.ensure_future(wrapper())


def create_task(coro):
    async def wrapper():
        await coro
        if _Logger.instance:
            _Logger.instance.flush()
    return asyncio.ensure_future(wrapper())
