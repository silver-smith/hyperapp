import asyncio
import logging
import time

log = logging.getLogger(__name__)


async def wait_for(timeout_sec, fn, *args, **kw):
    t = time.time()
    while not fn(*args, **kw):
        if time.time() - t > timeout_sec:
            assert False, 'Timed out in %s seconds' % timeout_sec
        await asyncio.sleep(0.1)


async def wait_for_all_tasks_to_complete(timeout_sec=1):
    t = time.time()
    future = asyncio.Future()
    def check_pending():
        pending = [task for task in asyncio.Task.all_tasks() if not task.done()]
        log.debug('%d pending tasks:', len(pending))
        for task in pending:
            log.debug('\t%s', task)
        if len(pending) > 1:  # only test itself must be left
            if time.time() - t > timeout_sec:
                future.set_exception(RuntimeError('Timed out waiting for all tasks to complete in %s seconds' % timeout_sec))
            else:
                asyncio.get_event_loop().call_soon(check_pending)
        else:
            future.set_result(None)
    asyncio.get_event_loop().call_soon(check_pending)
    await future
