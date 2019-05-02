import asyncio
from contextlib import contextmanager
import logging

import pytest

from hyperapp.common.logger import log, logger_inited

_log = logging.getLogger(__name__)


class StubStorage:

    def __init__(self):
        self.entries = []

    def add_entry(self, entry):
        self.entries.append(entry)

    def close(self):
        pass


@pytest.fixture
def init():

    @contextmanager
    def inited():
        storage = StubStorage()
        with logger_inited(storage):
            yield storage
        _log.info('storage.entries: %r', storage.entries)
        for entry in storage.entries:
            _log.info('Entry: %r', entry)

    return inited


def test_entry(init):
    with init() as storage:
        log.test_entry(foo='foo-value', bar='bar-value')
    assert storage.entries == [dict(
        type='entry',
        name='test_entry',
        foo='foo-value',
        bar='bar-value',
        )]


def test_context(init):
    with init() as storage:
        with log.test_context(foo='foo-value'):
            log.test_entry(bar='bar-value')
    context = storage.entries[0]['context']
    assert storage.entries == [
        dict(type='context-enter', name='test_context', foo='foo-value', context=context),
        dict(type='entry', name='test_entry', bar='bar-value', context=context),
        dict(type='context-exit', context=context),
        ]


def test_nested_context(init):
    with init() as storage:
        with log.root_context(foo='foo'):
            log.foo_entry(bar='bar')
            with log.nested_context(bar='bar'):
                log.inner_entry(foo='foo')
    context_1 = storage.entries[0]['context']
    context_2 = storage.entries[2]['context']
    assert storage.entries == [
        dict(type='context-enter', name='root_context', foo='foo', context=context_1),
        dict(type='entry', name='foo_entry', bar='bar', context=context_1),
        dict(type='context-enter', name='nested_context', bar='bar', context=context_2),
        dict(type='entry', name='inner_entry', foo='foo', context=context_2),
        dict(type='context-exit', context=context_2),
        dict(type='context-exit', context=context_1),
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
        entry['num']: entry['context'] for entry in storage.entries
        if entry['type'] == 'context-enter' and entry['name'] == 'level_1_context'}
    context_2_map = {
        entry['num']: entry['context'] for entry in storage.entries
        if entry['type'] == 'context-enter' and entry['name'] == 'level_2_context'}

    for num in range(1, 4):
        context_1 = context_1_map[num]
        context_2 = context_2_map[num]
        assert context_2[0] == context_1[0]
        assert [entry for entry in storage.entries if entry['context'] in [context_1, context_2]] == [
            dict(type='context-enter', name='level_1_context', num=num, context=context_1),
            dict(type='entry', name='level_1_entry', num=num, context=context_1),
            dict(type='context-enter', name='level_2_context', num=num, context=context_2),
            dict(type='entry', name='level_2_entry', num=num, context=context_2),
            dict(type='entry', name='level_3_entry', num=num, context=context_2),
            dict(type='context-exit', context=context_2),
            dict(type='context-exit', context=context_1),
            ]


def test_fn_decorator(init):

    @log
    def decorated_fn():
        log.inner(foo=1)

    with init() as storage:
        decorated_fn()
    context = storage.entries[0]['context']
    assert storage.entries == [
        dict(type='context-enter', name='decorated_fn', context=context),
        dict(type='entry', name='inner', foo=1, context=context),
        dict(type='context-exit', context=context),
        ]
