import logging
import inspect

log = logging.getLogger(__name__)


async def run_awaitable_factory(factory, *args, **kw):
    result = factory(*args, **kw)
    if inspect.isawaitable(result):
        return (await result)
    else:
        return result
