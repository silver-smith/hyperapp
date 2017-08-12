import pytest


class AsyncExceptionHandler(object):

    def __init__(self):
        self.had_exceptions = False

    def __call__(self, loop, context):
        self.had_exceptions = True
        loop.default_exception_handler(context)


@pytest.mark.hookwrapper
def pytest_pyfunc_call(pyfuncitem):
    event_loop = None
    for name in pyfuncitem._request.fixturenames:
        if name == 'event_loop':
            event_loop = pyfuncitem._request.getfixturevalue(name)
            break
    if event_loop:
        handler = AsyncExceptionHandler()
        event_loop.set_exception_handler(handler)
    outcome = yield
    passed = outcome.excinfo is None
    if passed and event_loop:
        assert not handler.had_exceptions, 'Event loop had unhandled exceptions'
