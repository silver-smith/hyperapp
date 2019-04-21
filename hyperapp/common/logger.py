from contextlib import contextmanager
import logging
import json

log = logging.getLogger(__name__)


class _LogFnAdapter:

    def __init__(self):
        pass

    def __getattr__(self, name):
        return _LoggerAdapter(name)


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

    def __init__(self, storage):
        self._storage = storage
        self._pending_entry = None
        self._context_name_stack = []

    def add_entry(self, entry):
        self.flush()
        self._pending_entry = entry

    def push_context(self):
        assert self._pending_entry
        entry = self._pending_entry
        self._pending_entry = None
        entry['type'] = 'context-enter'
        self._store_entry(entry)
        self._context_name_stack.append(entry['name'])

    def exit_context(self):
        self.flush()
        self._store_entry(dict(type='context-exit', name=self._context_name_stack[-1]))
        self._context_name_stack.pop()

    def flush(self):
        if self._pending_entry:
            self._store_entry(self._pending_entry)
            self._pending_entry = None

    def _store_entry(self, entry):
        self._storage.add_entry(entry)


@contextmanager
def logger_inited(storage):
    _Logger.instance = logger = _Logger(storage)
    yield
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
