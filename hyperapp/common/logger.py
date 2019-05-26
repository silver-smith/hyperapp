from collections import namedtuple
from contextlib import contextmanager
from enum import Enum
from functools import wraps
import inspect
import logging

import better_contextvars as contextvars

_log = logging.getLogger(__name__)


class RecordKind(Enum):
    LEAF = 1
    ENTER = 2
    EXIT = 3


class LogRecord(namedtuple('_LogRecordBase', 'kind context module_ref name params')):

    def __new__(cls, kind, context, module_ref=None, name=None, params=None):
        return super().__new__(cls, kind, context.copy(), module_ref, name, params or {})

    def clone_with(self, kind, context):
        return LogRecord(kind, context, self.module_ref, self.name, self.params)


def _module_vars(globals):
    try:
        return {'__module_ref__': globals['__module_ref__']}
    except KeyError:
        return {'__name__': globals['__name__']}


def _filter_params(params):
    return {name: value for name, value in params.items()
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
            module_vars = _module_vars(inspect.stack()[1].frame.f_globals)
            args_params = {
                param_names[idx]: arg
                for idx, arg in enumerate(args)
                }
            params = {**default_params, **args_params, **kw}
            logger = _Logger.get_instance()
            if logger:
                logger.enter_context(module_vars, fn.__qualname__, _filter_params(params))
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
        module_vars = _module_vars(inspect.stack()[1].frame.f_globals)
        logger = _Logger.get_instance()
        if logger:
            logger.add_entry(module_vars, self._record_name, kw)
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

    def __init__(self, module_ref_resolver, storage):
        self._module_ref_resolver = module_ref_resolver
        self._storage = storage
        self._context_counter = 0

    @with_flag_set(_inside_storage)
    def add_entry(self, module_vars, name, params):
        self._log('add_entry: %r %r %r', module_vars, name, params)
        self._flush()
        self._pending_record.set(
            self._make_record(RecordKind.LEAF, self._context, module_vars, name, params))

    @with_flag_set(_inside_storage)
    def enter_context(self, module_vars, name, params):
        self._log('enter_context: %r %r %r', module_vars, name, params)
        self._flush()
        self._context_counter += 1
        self._context.append(self._context_counter)
        self._store_record(
            self._make_record(RecordKind.ENTER, self._context, module_vars, name, params))

    @with_flag_set(_inside_storage)
    def push_context(self):
        self._log('push_context')
        record = self._pending_record.get()
        assert record
        self._pending_record.set(None)
        self._context_counter += 1
        self._context.append(self._context_counter)
        self._store_record(
            record.clone_with(RecordKind.ENTER, self._context))

    @with_flag_set(_inside_storage)
    def exit_context(self):
        self._log('exit_context')
        self._flush()
        assert self._context
        self._store_record(
            LogRecord(RecordKind.EXIT, self._context))
        self._context.pop()

    @with_flag_set(_inside_storage)
    def flush(self):
        self._flush()

    def _flush(self):
        pending_record = self._pending_record.get()
        if pending_record:
            self._store_record(pending_record)
            self._pending_record.set(None)

    def _make_record(self, kind, context, module_vars, name, params):
        module_ref = self._module_ref_resolver.get_module_ref(module_vars)
        return LogRecord(kind, context, module_ref, name, params)

    @property
    def _context(self):
        context = self._context_var.get()
        if context is None:
            context = []
            self._context_var.set(context)
        return context
        
    def _store_record(self, record):
        self._log('store record: %r', record)
        self._storage.add_record(record)

    def _log(self, format, *args):
        _log.debug('  logger (context=%r pending=%r) ' + format, self._context, self._pending_record.get(), *args)


def init_logger(module_ref_resolver, storage):
    _Logger.instance = _Logger(module_ref_resolver, storage)


def close_logger():
    logger = _Logger.instance
    _Logger.instance = None
    logger.flush()
