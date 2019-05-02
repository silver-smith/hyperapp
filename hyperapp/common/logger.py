from contextlib import contextmanager
from functools import wraps
import logging
import json

import better_contextvars as contextvars

_log = logging.getLogger(__name__)


class _LogFnAdapter:

    def __init__(self):
        pass

    def __getattr__(self, name):
        return _LoggerAdapter(name)

    def __call__(self, *args, **kw):
        assert len(args) == 1 and not kw and callable(args[0])
        fn = args[0]
        entry = dict(name=fn.__name__)

        @wraps(fn)
        def wrapper(*args, **kw):
            _Logger.instance.enter_context(entry)
            try:
                return fn(*args, **kw)
            finally:
                _Logger.instance.exit_context()

        return wrapper


log = _LogFnAdapter()


class _LoggerAdapter:

    def __init__(self, entry_name):
        self._entry_name = entry_name

    def __call__(self, **kw):
        entry = dict(
            type='entry',
            name=self._entry_name,
            **kw)
        _Logger.instance.add_entry(entry)
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
    _pending_entry = contextvars.ContextVar('logger_pending_entry', default=None)

    def __init__(self, storage):
        self._storage = storage
        self._context_counter = 0

    def add_entry(self, entry):
        self._log('add_entry: %r', entry)
        self.flush()
        if self._context:
            entry['context'] = self._context[:]
        self._pending_entry.set(entry)

    def push_context(self):
        self._log('push_context')
        assert self._pending_entry.get()
        entry = self._pending_entry.get()
        self._pending_entry.set(None)
        self._context_counter += 1
        self._context.append(self._context_counter)
        entry['type'] = 'context-enter'
        assert self._context
        entry['context'] = self._context[:]
        self._store_entry(entry)

    def enter_context(self, entry):
        self.add_entry(entry)
        self.push_context()

    def exit_context(self):
        self._log('exit_context')
        self.flush()
        assert self._context
        self._store_entry(dict(type='context-exit', context=self._context[:]))
        self._context.pop()

    def flush(self):
        if self._pending_entry.get():
            self._store_entry(self._pending_entry.get())
            self._pending_entry.set(None)

    @property
    def _context(self):
        context = self._context_var.get()
        if context is None:
            context = []
            self._context_var.set(context)
        return context

    def _store_entry(self, entry):
        self._log('store entry: %r', entry)
        self._storage.add_entry(entry)

    def _log(self, format, *args):
        _log.debug('  logger (context=%r pending=%r) ' + format, self._context, self._pending_entry.get(), *args)


@contextmanager
def logger_inited(storage):
    _Logger.instance = logger = _Logger(storage)
    yield
    _Logger.instance = None
    logger.flush()
    storage.close()


def json_file_log_storage(dir, start_time):
    path = dir.joinpath(start_time.strftime('%Y-%m-%d-%H-%M-%S')).with_suffix('.json')
    return _JsonFileLogStorage(path)

    
class _JsonFileLogStorage:

    def __init__(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._f = path.open('w')

    def close(self):
        self._f.close()

    def add_entry(self, entry):
        line = json.dumps(entry)
        self._f.write(line + '\n')
