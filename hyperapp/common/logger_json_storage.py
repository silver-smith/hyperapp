from datetime import datetime
from enum import Enum
import json
from pathlib import Path

from dateutil.tz import tzlocal

from .htypes import meta_ref_t, t_ref, t_field_meta, t_record_meta
from .htypes.deduce_value_type import DeduceTypeError, deduce_value_type
from .dict_encoders import DictEncoder
from .logger import RecordKind, LogRecord


JSON_LOGS_DIR = Path('~/.local/share/hyperapp/client/logs').expanduser()


class LineType(Enum):
    TYPE = 1
    LOG_RECORD = 2


def json_file_log_storage_session():
    start_time = datetime.now(tzlocal())
    path = JSON_LOGS_DIR.joinpath(start_time.strftime('%Y-%m-%d-%H-%M-%S')).with_suffix('.json')
    return _JsonFileLogStorage(path)



class _RecordsToLineConverter:

    def __init__(self, type_resolver, ref_registry):
        self._type_resolver = type_resolver
        self._ref_registry = ref_registry
        self._dict_encoder = DictEncoder()

    def record2lines(self, record):
        type_capsule, params_t = self._make_params_type(record.name, record.params)
        yield json.dumps(dict(
            line_type=LineType.TYPE.name,
            type_capsule=self._to_dict(type_capsule),
            ))
        yield json.dumps(dict(
            line_type=LineType.LOG_RECORD.name,
            kind=record.kind.name,
            context=record.context,
            name=record.name,
            params=self._to_dict(params_t(**record.params)),
            ))

    def _to_dict(self, value):
        return self._dict_encoder.encode(value)

    def _make_params_type(self, type_name, params):
        fields = []
        for name, value in params.items():
            try:
                t = deduce_value_type(value)
            except DeduceTypeError:
                continue
            type_ref = self._type_resolver.reverse_resolve(t)
            fields.append(t_field_meta(name, t_ref(type_ref)))
        rec = meta_ref_t(type_name, t_record_meta(fields))
        capsule, type_ref = self._ref_registry.register_object_to_capsule_and_ref(rec)
        params_t = self._type_resolver.resolve(type_ref)
        return (capsule, params_t)


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
