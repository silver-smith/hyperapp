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


def json_file_log_storage_session(type_resolver, ref_registry):
    converter = _RecordsJsonEncoder(type_resolver, ref_registry)
    start_time = datetime.now(tzlocal())
    path = JSON_LOGS_DIR.joinpath(start_time.strftime('%Y-%m-%d-%H-%M-%S')).with_suffix('.json')
    return _JsonFileLogStorage(converter, path)



class _RecordsJsonEncoder:

    def __init__(self, type_resolver, ref_registry):
        self._type_resolver = type_resolver
        self._ref_registry = ref_registry
        self._dict_encoder = DictEncoder()
        self._stored_type_refs = set()

    def record2lines(self, record):
        if record.kind != RecordKind.EXIT:
            type_capsule, params_type_ref, params_t = self._make_params_type(record.name, record.params)
            if params_type_ref not in self._stored_type_refs:
                yield json.dumps(dict(
                    line_type=LineType.TYPE.name,
                    type_capsule=self._to_dict(type_capsule),
                    ))
                self._stored_type_refs.add(params_type_ref)
            # remove params those type we were unable to deduce
            params_fields = {
                name: value for name, value in record.params.items()
                if name in params_t.fields}
            params_dict = self._to_dict(params_t(**params_fields))
        else:
            params_type_ref = None
            params_dict = None
        yield json.dumps(dict(
            line_type=LineType.LOG_RECORD.name,
            kind=record.kind.name,
            context=record.context,
            name=record.name,
            params_type_ref=self._to_dict(params_type_ref) if params_type_ref else None,
            params=params_dict,
            ))

    def _to_dict(self, value):
        return self._dict_encoder.encode(value)

    def _make_params_type(self, type_name, params):
        field_values = {}
        fields = []
        for name, value in params.items():
            try:
                t = deduce_value_type(value)
            except DeduceTypeError:
                continue
            type_ref = self._type_resolver.reverse_resolve(t)
            fields.append(t_field_meta(name, t_ref(type_ref)))
            field_values[name] = value
        rec = meta_ref_t(type_name.replace('.', '_'), t_record_meta(fields))
        capsule, type_ref = self._ref_registry.register_object_to_capsule_and_ref(rec)
        params_t = self._type_resolver.resolve(type_ref)
        return (capsule, type_ref, params_t)


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
        params_type_ref = self._dict_decoder.decode_dict(ref_t, d['params_type_ref'])
        params_t = self._type_resolver.resolve(params_type_ref)
        params = self._dict_decoder.decode_dict(params_t, d['params'])
        return LogRecord(
            kind=RecordKind[d['kind']],
            context=d['context'],
            name=d['name'],
            params=params,
            )


class _JsonFileLogStorage:

    def __init__(self, converter, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.session = path.stem
        self._f = path.open('w')
        self._converter = converter

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
