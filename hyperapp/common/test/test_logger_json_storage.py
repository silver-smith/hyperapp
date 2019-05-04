import logging

import pytest

from hyperapp.common.htypes import register_builtin_types
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


def test_record_to_line_converter(type_resolver, ref_registry):
    storage = _RecordsToLineConverter(type_resolver, ref_registry)
    record = LogRecord(RecordKind.ENTER, [1, 2], 'context_enter', dict(num=123, name='sam'))
    for line in storage.record2lines(record):
        _log.info("storage line: %r", line)
