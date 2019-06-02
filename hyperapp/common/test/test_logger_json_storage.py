import logging
from types import SimpleNamespace

import pytest

from hyperapp.common.util import flatten
from hyperapp.common.htypes import tInt, tString, meta_ref_t, t_ref, t_field_meta, t_record_meta, ref_t, register_builtin_types
from hyperapp.common.ref_resolver import RefResolver
from hyperapp.common.type_resolver import TypeResolver
from hyperapp.common.ref_registry import RefRegistry
from hyperapp.common.logger import RecordKind, LogRecord
from hyperapp.common.logger_json_storage import _RecordsJsonEncoder, _RecordsJsonDecoder
from hyperapp.common import cdr_coders  # register codec

_log = logging.getLogger(__name__)


@pytest.fixture
def ref_resolver():
    return RefResolver()


@pytest.fixture
def type_resolver(ref_resolver):
    return TypeResolver(ref_resolver)


@pytest.fixture
def ref_registry(ref_resolver, type_resolver):
    registry = RefRegistry(type_resolver)
    register_builtin_types(registry, type_resolver)
    ref_resolver.add_source(registry)
    return registry


@pytest.fixture
def encoder(ref_resolver, type_resolver):
    return _RecordsJsonEncoder(ref_resolver, type_resolver)


@pytest.fixture
def decoder(type_resolver, ref_registry):
    return _RecordsJsonDecoder(type_resolver, ref_registry)


@pytest.fixture
def types(type_resolver, ref_registry):
    primitive_params = type_resolver.register_type(ref_registry, meta_ref_t('primitive_params', t_record_meta([
        t_field_meta('num', t_ref(type_resolver.reverse_resolve(tInt))),
        t_field_meta('name', t_ref(type_resolver.reverse_resolve(tString))),
        ]))).t
    ref_params = type_resolver.register_type(ref_registry, meta_ref_t('primitive_params', t_record_meta([
        t_field_meta('test_ref', t_ref(type_resolver.reverse_resolve(ref_t))),
        ]))).t
    return SimpleNamespace(
        primitive_params=primitive_params,
        ref_params=ref_params,
        )


def test_primitives(encoder, decoder, types):
    record_1 = LogRecord(RecordKind.ENTER, [1, 2], None, 'context_enter', types.primitive_params(num=123, name='sam'))
    record_2 = LogRecord(RecordKind.ENTER, [1, 3], None, 'context_enter', types.primitive_params(num=456, name='mike'))
    line_list = list(encoder.record2lines(record_1)) + list(encoder.record2lines(record_2))
    for line in line_list:
        _log.info("storage line: %r", line)
    assert len(line_list) == 3  # type should be reused
    records = flatten(decoder.decode_line(line) for line in line_list)
    assert len(records) == 2
    assert records[0].kind == RecordKind.ENTER
    assert records[0].params.num == 123
    assert records[1].params.name == 'mike'


def test_ref(encoder, decoder, types):
    test_ref = ref_t('sha-whatever', b'some-hash')
    record = LogRecord(RecordKind.ENTER, [1, 2], None, 'context_enter', types.ref_params(test_ref=test_ref))
    line_list = list(encoder.record2lines(record))
    for line in line_list:
        _log.info("storage line: %r", line)
    records = flatten(decoder.decode_line(line) for line in line_list)
    assert records[0].params.test_ref == test_ref
    assert records[0].params.test_ref is not test_ref
