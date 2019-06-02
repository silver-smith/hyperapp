from datetime import datetime
from enum import Enum
import json
from pathlib import Path

from dateutil.tz import tzlocal

from .htypes import meta_ref_t, t_ref, t_field_meta, t_record_meta, ref_t, capsule_t
from .htypes.deduce_value_type import DeduceTypeError, deduce_value_type
from .dict_encoders import DictEncoder
from .dict_decoders import DictDecoder
from .logger import RecordKind, LogRecord


JSON_LOGS_DIR = Path('~/.local/share/hyperapp/client/logs').expanduser()


class LineType(Enum):
    TYPE = 1
    LOG_RECORD = 2


def json_file_log_storage_session(ref_resolver, type_resolver):
    encoder = _RecordsJsonEncoder(ref_resolver, type_resolver)
    start_time = datetime.now(tzlocal())
    path = JSON_LOGS_DIR.joinpath(start_time.strftime('%Y-%m-%d-%H-%M-%S')).with_suffix('.json')
    return _JsonFileLogStorage(encoder, path)



class _RecordsJsonEncoder:

    def __init__(self, ref_resolver, type_resolver):
        self._ref_resolver = ref_resolver
        self._type_resolver = type_resolver
        self._dict_encoder = DictEncoder()
        self._stored_type_refs = set()

    def record2lines(self, record):
        encoder = self._dict_encoder
        params = record.params
        if params:
            params_t = params._t
            params_type_ref = self._type_resolver.reverse_resolve(params_t)
            if params_type_ref not in self._stored_type_refs:
                capsule = self._ref_resolver.resolve_ref(params_type_ref)
                yield json.dumps(dict(
                    line_type=LineType.TYPE.name,
                    type_capsule=encoder.encode(capsule),
                    ))
                self._stored_type_refs.add(params_type_ref)
        yield json.dumps(dict(
            line_type=LineType.LOG_RECORD.name,
            kind=record.kind.name,
            context=record.context,
            module_ref=encoder.encode(record.module_ref) if record.module_ref else None,
            name=record.name,
            params_type_ref=encoder.encode(params_type_ref) if params else None,
            params=encoder.encode(params) if params else None,
            ))


class _RecordsJsonDecoder:

    def __init__(self, type_resolver, ref_registry):
        self._type_resolver = type_resolver
        self._ref_registry = ref_registry
        self._dict_decoder = DictDecoder()

    def decode_line(self, line):
        d = json.loads(line)
        line_type = LineType[d['line_type']]
        if line_type == LineType.TYPE:
            self._process_type(d)
        elif line_type == LineType.LOG_RECORD:
            yield self._process_record(d)
        else:
            assert 0, repr(line_type)  # Unexpected line type

    def _process_type(self, d):
        type_capsule = self._dict_decoder.decode_dict(capsule_t, d['type_capsule'])
        self._ref_registry.register_capsule(type_capsule)

    def _process_record(self, d):
        params_type_ref_encoded = d['params_type_ref']
        if params_type_ref_encoded is not None:
            params_type_ref = self._dict_decoder.decode_dict(ref_t, params_type_ref_encoded)
            params_t = self._type_resolver.resolve(params_type_ref)
            params = self._dict_decoder.decode_dict(params_t, d['params'])
        else:
            params = None
        return LogRecord(
            kind=RecordKind[d['kind']],
            context=d['context'],
            name=d['name'],
            params=params,
            )


class _JsonFileLogStorage:

    def __init__(self, encoder, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.session = path.stem
        self._f = path.open('w')
        self._encoder = encoder

    def close(self):
        self._f.close()

    def add_record(self, record):
        for line in self._encoder.record2lines(record):
            self._f.write(line + '\n')


class JsonFileLogStorageReader:

    def __init__(self, type_resolver, ref_registry, session):
        self.session = session
        self._decoder = _RecordsJsonDecoder(type_resolver, ref_registry)

    def enumerate_entries(self):
        with JSON_LOGS_DIR.joinpath(self.session).with_suffix('.json').open() as f:
            while True:
                line = f.readline()
                if not line:
                    return
                yield from self._decoder.decode_line(line)


def json_storage_session_list():
    return sorted(path.stem for path in JSON_LOGS_DIR.glob('*.json'))
