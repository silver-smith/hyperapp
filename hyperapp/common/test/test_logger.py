import asyncio
from contextlib import contextmanager
import logging

import pytest

from hyperapp.common.logger import RecordKind, LogRecord, log, init_logger, close_logger

_log = logging.getLogger(__name__)


class StubStorage:

    def __init__(self):
        self.records = []

    def add_record(self, record):
        self.records.append(record)


@pytest.fixture
def init():

    @contextmanager
    def inited():
        storage = StubStorage()
        init_logger(storage)
        yield storage
        close_logger()
        _log.info('storage.records: %r', storage.records)
        for record in storage.records:
            _log.info('Record: %r', record)

    return inited


def test_entry(init):
    with init() as storage:
        log.test_entry(foo='foo-value', bar='bar-value')
    assert storage.records == [LogRecord(
        kind=RecordKind.LEAF,
        context=[],
        name='test_entry',
        params=dict(foo='foo-value', bar='bar-value'),
        )]


def test_context(init):
    with init() as storage:
        with log.test_context(foo='foo-value'):
            log.test_entry(bar='bar-value')
    context = storage.records[0].context
    assert storage.records == [
        LogRecord(RecordKind.ENTER, context, 'test_context', dict(foo='foo-value')),
        LogRecord(RecordKind.LEAF, context, 'test_entry', dict(bar='bar-value')),
        LogRecord(RecordKind.EXIT, context, None, {}),
        ]


def test_nested_context(init):
    with init() as storage:
        with log.root_context(foo='foo'):
            log.foo_entry(bar='bar')
            with log.nested_context(bar='bar'):
                log.inner_entry(foo='foo')
    context_1 = storage.records[0].context
    context_2 = storage.records[2].context
    assert storage.records == [
        LogRecord(RecordKind.ENTER, context_1, 'root_context', dict(foo='foo')),
        LogRecord(RecordKind.LEAF, context_1, 'foo_entry', dict(bar='bar')),
        LogRecord(RecordKind.ENTER, context_2, 'nested_context', dict(bar='bar')),
        LogRecord(RecordKind.LEAF, context_2, 'inner_entry', dict(foo='foo')),
        LogRecord(RecordKind.EXIT, context_2, None, {}),
        LogRecord(RecordKind.EXIT, context_1, None, {}),
        ]


class Barrier:

    def __init__(self, parties):
        self._wanted_entries = parties
        self._cond = asyncio.Condition()

    async def wait(self):
        async with self._cond:
            self._wanted_entries -= 1
            await self._cond.wait_for(lambda: self._wanted_entries == 0)
            self._cond.notify_all()


@pytest.mark.asyncio
async def test_async_context(init):

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
            await level_1_barrier.wait()
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
            LogRecord(RecordKind.ENTER, context_1, 'level_1_context', dict(num=num)),
            LogRecord(RecordKind.LEAF, context_1, 'level_1_entry', dict(num=num)),
            LogRecord(RecordKind.ENTER, context_2, 'level_2_context', dict(num=num)),
            LogRecord(RecordKind.LEAF, context_2, 'level_2_entry', dict(num=num)),
            LogRecord(RecordKind.LEAF, context_2, 'level_3_entry', dict(num=num)),
            LogRecord(RecordKind.EXIT, context_2, None, {}),
            LogRecord(RecordKind.EXIT, context_1, None, {}),
            ]


@log
def decorated_fn():
    log.inner(foo=1)


def test_fn_decorator(init):
    with init() as storage:
        decorated_fn()
    context = storage.records[0].context
    assert storage.records == [
        LogRecord(RecordKind.ENTER, context, 'decorated_fn', {}),
        LogRecord(RecordKind.LEAF, context, 'inner', dict(foo=1)),
        LogRecord(RecordKind.EXIT, context, None, {}),
        ]


@log
def decorated_fn_with_args(foo, bar, baz=789):
    log.inner(foo=foo)


def test_fn_decorator_args(init):
    with init() as storage:
        decorated_fn_with_args(123, bar=456)
    context = storage.records[0].context
    assert storage.records == [
        LogRecord(RecordKind.ENTER, context, 'decorated_fn_with_args', dict(foo=123, bar=456, baz=789)),
        LogRecord(RecordKind.LEAF, context, 'inner', dict(foo=123)),
        LogRecord(RecordKind.EXIT, context, None, {}),
        ]


class TestClass:

    @log
    def method(self, foo, bar, baz=789):
        log.inner(foo=foo)


def test_method_decorator_args(init):
    with init() as storage:
        TestClass().method(123, bar=456)
    context = storage.records[0].context
    assert storage.records == [
        LogRecord(RecordKind.ENTER, context, 'TestClass.method', dict(foo=123, bar=456, baz=789)),
        LogRecord(RecordKind.LEAF, context, 'inner', dict(foo=123)),
        LogRecord(RecordKind.EXIT, context, None, {}),
        ]
