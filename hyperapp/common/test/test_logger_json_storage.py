import logging

import pytest

from hyperapp.common.htypes import ref_t, register_builtin_types
from hyperapp.common.ref_resolver import RefResolver
from hyperapp.common.type_resolver import TypeResolver
from hyperapp.common.ref_registry import RefRegistry
from hyperapp.common.logger import RecordKind, LogRecord
from hyperapp.common.logger_json_storage import _RecordsToLineConverter
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
def converter(type_resolver, ref_registry):
    return _RecordsToLineConverter(type_resolver, ref_registry)


def test_primitives(converter):
    record_1 = LogRecord(RecordKind.ENTER, [1, 2], 'context_enter', dict(num=123, name='sam'))
    for line in converter.record2lines(record_1):
        _log.info("storage line: %r", line)
    record_2 = LogRecord(RecordKind.ENTER, [1, 3], 'context_enter', dict(num=456, name='mike'))
    assert len(list(converter.record2lines(record_2))) == 1  # type should be reused


def test_ref(converter):
    record = LogRecord(RecordKind.ENTER, [1, 2], 'context_enter', dict(test_ref=ref_t('sha-whatever', b'some-hash')))
    for line in converter.record2lines(record):
        _log.info("storage line: %r", line)
