import logging
import traceback

log = logging.getLogger(__name__)


def mp2async_future(event_loop, thread_pool, mp_future, timeout_sec=3):
    return mp2async(event_loop, thread_pool, mp_future.result, timeout_sec)

def mp2async(event_loop, thread_pool, get_result_fn, timeout_sec=3):
    async_future = event_loop.create_future()
    def handle_result():
        log.debug('mp2async_future.handle_result: started')
        try:
            result = get_result_fn(timeout=timeout_sec)
            log.debug('mp2async_future.handle_result: result=%r', result)
            event_loop.call_soon_threadsafe(async_future.set_result, result)
            log.debug('mp2async_future.handle_result: succeeded')
        except Exception as x:
            log.exception('mp2async_future.handle_result:')
            event_loop.call_soon_threadsafe(async_future.set_exception, x)
    thread_pool.submit(handle_result)
    log.debug('mp2async_future: ready')
    return async_future

def mp_call_async(event_loop, thread_pool, mp_pool, method, args, timeout_sec=3):
    log.debug('mp_call_async: %r(%r)', method, args)
    async_result = mp_pool.apply_async(method, args)
    return mp2async(event_loop, thread_pool, async_result.get, timeout_sec)


class ServerProcess(object):

    instance = None

    @classmethod
    def construct(cls, *args, **kw):
        cls.instance = cls(*args, **kw)

    @classmethod
    def _call(cls, method, *args, **kw):
        try:
            return method(cls.instance, *args, **kw)
        except:
            traceback.print_exc()
            raise

    @classmethod
    def call(cls, mp_pool, method, *args):
        return mp_pool.apply(cls._call, (method,) + args)

    @classmethod
    def async_call(cls, event_loop, thread_pool, mp_pool, method, *args):
        return mp_call_async(event_loop, thread_pool, mp_pool, cls._call, (method,) + args)
