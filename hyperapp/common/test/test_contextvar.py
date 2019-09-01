import asyncio
import contextvars
import logging

import pytest

from hyperapp.common.test.barrier import Barrier

_log = logging.getLogger(__name__)


_context = contextvars.ContextVar('test_context', default=None)


@pytest.mark.asyncio
async def test_async_context():

    level_1_barrier = Barrier(3)
    level_2_barrier = Barrier(3)
    level_3_barrier = Barrier(3)

    async def level_3(num):
        _log.info('level_3 %r', num)
        await level_3_barrier.wait()
        assert _context.get() == num * 10
        _log.info('level_3 %r finished', num)

    async def level_2(num):
        _log.info('level_2 %r', num)
        assert _context.get() == num
        _context.set(num * 10)
        await level_2_barrier.wait()
        await level_3(num)
        _log.info('level_2 %r finished', num)

    async def level_1(num):
        _log.info('level_1 %r', num)
        assert not _context.get()
        _context.set(num)
        await level_1_barrier.wait()
        await level_2(num)
        _log.info('level_1 %r finished', num)

    await asyncio.gather(level_1(1), level_1(2), level_1(3))
