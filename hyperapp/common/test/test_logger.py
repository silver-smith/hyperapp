import asyncio
from contextlib import contextmanager
import logging

import pytest

from hyperapp.common.htypes import register_builtin_types
from hyperapp.common.code_module import register_code_module_types
from hyperapp.common.ref_registry import RefRegistry
from hyperapp.common.ref_resolver import RefResolver
from hyperapp.common.type_resolver import TypeResolver
from hyperapp.common.module_ref_resolver import ModuleRefResolver
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.logger import RecordKind, LogRecord, log, init_logger, close_logger
from hyperapp.common.test.barrier import Barrier

_log = logging.getLogger(__name__)


class StubStorage:

    def __init__(self):
        self._records = []

    def add_record(self, record):
        self._records.append(record)

    @property
    def records(self):
        return [LogRecord(r.kind, r.context, r.module_ref, r.name, r.params._asdict() if r.params else r.params)
                for r in self._records]


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
    register_code_module_types(registry, type_resolver)
    ref_resolver.add_source(registry)
    return registry


@pytest.fixture
def module_ref_resolver(ref_registry):
    return ModuleRefResolver(ref_registry)


@pytest.fixture
def this_module_ref(module_ref_resolver):
    return module_ref_resolver.get_module_ref({'__name__': __name__})


@pytest.fixture
def init(type_resolver, ref_registry, module_ref_resolver):

    @contextmanager
    def inited():
        storage = StubStorage()
        logger = init_logger(type_resolver, ref_registry, module_ref_resolver, storage)
        logger.init_asyncio_task_factory()
        yield storage
        close_logger()
        _log.info('storage.records: %r', storage.records)
        for record in storage.records:
            _log.info('Record: %r', record)

    return inited


def test_entry(this_module_ref, init):
    with init() as storage:
        log.test_entry_1(foo='foo-value-1')
        log.test_entry_2(foo='foo-value-2', bar='bar-value')
    assert storage.records == [
        LogRecord(RecordKind.LEAF, [], this_module_ref, 'test_entry_1', dict(foo='foo-value-1')),
        LogRecord(RecordKind.LEAF, [], this_module_ref, 'test_entry_2', dict(foo='foo-value-2', bar='bar-value')),
        ]


def test_context(this_module_ref, init):
    with init() as storage:
        with log.test_context(foo='foo-value'):
            log.test_entry(bar='bar-value')
    context = storage.records[0].context
    assert storage.records == [
        LogRecord(RecordKind.ENTER, context, this_module_ref, 'test_context', dict(foo='foo-value')),
        LogRecord(RecordKind.LEAF, context, this_module_ref, 'test_entry', dict(bar='bar-value')),
        LogRecord(RecordKind.EXIT, context),
        ]


def test_nested_context(this_module_ref, init):
    with init() as storage:
        with log.root_context(foo='foo'):
            log.foo_entry(bar='bar')
            with log.nested_context(bar='bar'):
                log.inner_entry(foo='foo')
    context_1 = storage.records[0].context
    context_2 = storage.records[2].context
    assert storage.records == [
        LogRecord(RecordKind.ENTER, context_1, this_module_ref, 'root_context', dict(foo='foo')),
        LogRecord(RecordKind.LEAF,  context_1, this_module_ref, 'foo_entry', dict(bar='bar')),
        LogRecord(RecordKind.ENTER, context_2, this_module_ref, 'nested_context', dict(bar='bar')),
        LogRecord(RecordKind.LEAF,  context_2, this_module_ref, 'inner_entry', dict(foo='foo')),
        LogRecord(RecordKind.EXIT,  context_2),
        LogRecord(RecordKind.EXIT,  context_1),
        ]


@pytest.mark.asyncio
async def test_async_context(this_module_ref, init):

    level_1_barrier = Barrier(3)
    level_2_barrier = Barrier(3)
    level_3_barrier = Barrier(3)

    async def level_3(num):
        _log.info('level_3 %r', num)
        await level_3_barrier.wait()
        log.level_3_entry(num=num)
        _log.info('level_3 %r finished', num)

    async def level_2(num):
        _log.info('level_2 %r', num)
        with log.level_2_context(num=num):
            await level_2_barrier.wait()
            log.level_2_entry(num=num)
            await level_3(num)
        _log.info('level_2 %r finished', num)

    async def level_1(num):
        _log.info('level_1 %r', num)
        with log.level_1_context(num=num):
            _log.info('level_1 %r: entered context, wait barrier', num)
            await level_1_barrier.wait()
            _log.info('level_1 %r: got barrier, wait level2', num)
            log.level_1_entry(num=num)
            await level_2(num)
        _log.info('level_1 %r finished', num)

    with init() as storage:
        await asyncio.gather(level_1(1), level_1(2), level_1(3))

    context_1_map = {
        record.params['num']: record.context for record in storage.records
        if record.kind == RecordKind.ENTER and record.name == 'level_1_context'}
    context_2_map = {
        record.params['num']: record.context for record in storage.records
        if record.kind == RecordKind.ENTER and record.name == 'level_2_context'}

    for num in range(1, 4):
        context_1 = context_1_map[num]
        context_2 = context_2_map[num]
        assert context_2[0] == context_1[0]
        assert [record for record in storage.records if record.context in [context_1, context_2]] == [
            LogRecord(RecordKind.ENTER, context_1, this_module_ref, 'level_1_context', dict(num=num)),
            LogRecord(RecordKind.LEAF,  context_1, this_module_ref, 'level_1_entry', dict(num=num)),
            LogRecord(RecordKind.ENTER, context_2, this_module_ref, 'level_2_context', dict(num=num)),
            LogRecord(RecordKind.LEAF,  context_2, this_module_ref, 'level_2_entry', dict(num=num)),
            LogRecord(RecordKind.LEAF,  context_2, this_module_ref, 'level_3_entry', dict(num=num)),
            LogRecord(RecordKind.EXIT,  context_2),
            LogRecord(RecordKind.EXIT,  context_1),
            ]


@pytest.mark.asyncio
async def test_async_task(this_module_ref, init):

    async def task():
        log.test_entry(foo=123)

    with init() as storage:
        future = asyncio.ensure_future(task())
        await future

    assert storage.records == [
        LogRecord(RecordKind.LEAF, [], this_module_ref, 'test_entry', dict(foo=123)),
        ]


@log
def decorated_fn():
    log.inner(foo=1)


def test_fn_decorator(this_module_ref, init):
    with init() as storage:
        decorated_fn()
    context = storage.records[0].context
    assert storage.records == [
        LogRecord(RecordKind.ENTER, context, this_module_ref, 'decorated_fn', {}),
        LogRecord(RecordKind.LEAF,  context, this_module_ref, 'inner', dict(foo=1)),
        LogRecord(RecordKind.EXIT,  context),
        ]


@log
def decorated_fn_with_args(foo, bar, baz=789):
    log.inner(foo=foo)


def test_fn_decorator_args(this_module_ref, init):
    with init() as storage:
        decorated_fn_with_args(123, bar=456)
    context = storage.records[0].context
    assert storage.records == [
        LogRecord(RecordKind.ENTER, context, this_module_ref, 'decorated_fn_with_args', dict(foo=123, bar=456, baz=789)),
        LogRecord(RecordKind.LEAF,  context, this_module_ref, 'inner', dict(foo=123)),
        LogRecord(RecordKind.EXIT,  context),
        ]


class TestClass:

    @log
    def method(self, foo, bar, baz=789):
        log.inner(foo=foo)


def test_method_decorator_args(this_module_ref, init):
    with init() as storage:
        TestClass().method(123, bar=456)
    context = storage.records[0].context
    assert storage.records == [
        LogRecord(RecordKind.ENTER, context, this_module_ref, 'TestClass.method', dict(foo=123, bar=456, baz=789)),
        LogRecord(RecordKind.LEAF,  context, this_module_ref, 'inner', dict(foo=123)),
        LogRecord(RecordKind.EXIT,  context),
        ]
