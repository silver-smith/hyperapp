from contextlib import contextmanager
import json


class LogFnAdapter:

    def __init__(self):
        pass

    def __getattr__(self, name):
        return LoggerAdapter(name)


log = LogFnAdapter()


class LoggerAdapter:

    def __init__(self, entry_name):
        self._entry_name = entry_name

    def __call__(self, **kw):
        entry = dict(
            name=self._entry_name,
            **kw)
        _storage.add_entry(entry)


_storage = None

def set_log_storage(storage):
    global _storage
    _storage = storage


@contextmanager
def json_file_log_storage(dir, start_time):
    path = dir.joinpath(start_time.strftime('%Y-%m-%d-%H-%M-%S')).with_suffix('.json')
    storage = JsonFileLogStorage(path)
    yield storage
    storage.close()

    
class JsonFileLogStorage:

    def __init__(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._f = path.open('w')

    def close(self):
        self._f.close()

    def add_entry(self, entry):
        line = json.dumps(entry)
        self._f.write(line + '\n')
