from datetime import datetime
import json
from pathlib import Path

from dateutil.tz import tzlocal

from .logger import RecordKind, LogRecord


JSON_LOGS_DIR = Path('~/.local/share/hyperapp/client/logs').expanduser()


def json_file_log_storage_session():
    start_time = datetime.now(tzlocal())
    path = JSON_LOGS_DIR.joinpath(start_time.strftime('%Y-%m-%d-%H-%M-%S')).with_suffix('.json')
    return _JsonFileLogStorage(path)



class _RecordsToLineConverter:

    def __init__(self):
        pass

    def record2lines(self, record):
        d = record._asdict()
        d['kind'] = record.kind.name
        return [json.dumps(d)]


class _JsonFileLogStorage:

    def __init__(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.session = path.stem
        self._f = path.open('w')
        self._converter = _RecordsToLineConverter()

    def close(self):
        self._f.close()

    def add_record(self, record):
        for line in self._converter.record2lines(record):
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
                yield LogRecord(kind, d['context'], d['name'], d['params'])


def json_storage_session_list():
    return sorted(path.stem for path in JSON_LOGS_DIR.glob('*.json'))
