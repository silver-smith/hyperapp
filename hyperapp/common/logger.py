from collections import namedtuple
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from functools import wraps
import inspect
import logging
import json
from pathlib import Path

from dateutil.tz import tzlocal

import better_contextvars as contextvars

_log = logging.getLogger(__name__)


JSON_LOGS_DIR = Path('~/.local/share/hyperapp/client/logs').expanduser()


class RecordKind(Enum):
    LEAF = 1
    ENTER = 2
    EXIT = 3


class _LogRecord(namedtuple('_LogRecord', 'kind context name params')):

    def with_kind(self, kind):
        return _LogRecord(kind, self.context, self.name, self.params)

    def with_context(self, context):
        return _LogRecord(self.kind, context[:], self.name, self.params)


def _make_record(name, params, kind=RecordKind.LEAF, context=None):
    return _LogRecord(kind, context[:] if context else [], name, {name: str(value) for name, value in params.items()})


def _exit_record(context, params=None):
    return _make_record(None, params or {}, RecordKind.EXIT, context)


class _LogFnAdapter:

    def __init__(self):
        pass

    def __getattr__(self, name):
        return _LoggerAdapter(name)

    def __call__(self, *args, **kw):
        assert len(args) == 1 and not kw and callable(args[0])
        fn = args[0]
        sig = inspect.signature(fn)

        @wraps(fn)
        def wrapper(*args, **kw):
            params = {
                name: parameter.default
                for name, parameter in sig.parameters.items()
                if parameter.default is not inspect.Parameter.empty
                }
            params.update({
                name: args[idx]
                for idx, name in enumerate(sig.parameters)
                if idx < len(args)
                })
            params.update({    
                name: kw[name]
                for name in sig.parameters
                if name in kw
                })
            record = _make_record(fn.__qualname__, params, kind=RecordKind.ENTER)
            if _Logger.instance:
                _Logger.instance.enter_context(record)
            try:
                return fn(*args, **kw)
            finally:
                if _Logger.instance:
                    _Logger.instance.exit_context()

        return wrapper


log = _LogFnAdapter()


class _LoggerAdapter:

    def __init__(self, record_name):
        self._record_name = record_name

    def __call__(self, **kw):
        record = _make_record(self._record_name, kw)
        _Logger.instance.add_entry(record)
        return _ContextAdapter()


class _ContextAdapter:

    def __init__(self):
        pass

    def __enter__(self):
        _Logger.instance.push_context()

    def __exit__(self, exc, value, tb):
        _Logger.instance.exit_context()


class _Logger:

    instance = None
    _context_var = contextvars.ContextVar('logger_context', default=None)
    _pending_record = contextvars.ContextVar('logger_pending_record', default=None)

    def __init__(self, storage):
        self._storage = storage
        self._context_counter = 0

    def add_entry(self, record):
        self._log('add_entry: %r', record)
        self.flush()
        self._pending_record.set(record.with_context(self._context))

    def push_context(self):
        self._log('push_context')
        assert self._pending_record.get()
        record = self._pending_record.get()
        self._pending_record.set(None)
        self._context_counter += 1
        self._context.append(self._context_counter)
        assert self._context
        self._store_record(
            record
            .with_kind(RecordKind.ENTER)
            .with_context(self._context))

    def enter_context(self, record):
        self.add_entry(record)
        self.push_context()

    def exit_context(self):
        self._log('exit_context')
        self.flush()
        assert self._context
        self._store_record(_exit_record(self._context))
        self._context.pop()

    def flush(self):
        if self._pending_record.get():
            self._store_record(self._pending_record.get())
            self._pending_record.set(None)

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


_current_session_storage = None


@contextmanager
def logger_inited(storage):
    global _current_session_storage

    _current_session_storage = storage
    _Logger.instance = logger = _Logger(storage)
    yield
    _Logger.instance = None
    logger.flush()
    storage.close()
    _current_session_storage = None


def json_file_log_storage_session():
    start_time = datetime.now(tzlocal())
    path = JSON_LOGS_DIR.joinpath(start_time.strftime('%Y-%m-%d-%H-%M-%S')).with_suffix('.json')
    return _JsonFileLogStorage(path)

    
class _JsonFileLogStorage:

    def __init__(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.session = path.stem
        self._f = path.open('w')

    def close(self):
        self._f.close()

    def add_record(self, record):
        d = record._asdict()
        d['kind'] = record.kind.name
        line = json.dumps(d)
        self._f.write(line + '\n')


class JsonFileLogStorageReader:

    def __init__(self, session):
        self.session = session

    def enumerate_entries(self):
        with JSON_LOGS_DIR.joinpath(self.session).with_suffix('.json').open() as f:
            while True:
                line = f.readline()
                if not line:
                    return
                d = json.loads(line)
                kind = RecordKind[d['kind']]
                yield _LogRecord(kind, d['context'], d['name'], d['params'])


def json_storage_session_list():
    return sorted(path.stem for path in JSON_LOGS_DIR.glob('*.json'))
