import logging
import pytest

from hyperapp.common.init_logging import get_logging_context


class AsyncExceptionHandler(object):

    def __init__(self):
        self.had_exceptions = False

    def __call__(self, loop, context):
        self.had_exceptions = True
        loop.default_exception_handler(context)


def setup_filter():

    def filter(record):
        record.context = get_logging_context()
        return True

    for handler in logging.getLogger().handlers:
        handler.addFilter(filter)


def pytest_configure(config):
    if config.getvalue('capture') == 'no':
        # when capturing stdout dump log to stdout too
        format = '%(asctime)s %(processName)-17s %(filename)-25s %(lineno)4d %(levelname)-8s %(message)s'
        logging.basicConfig(level=logging.DEBUG, format=format)
    else:
        logging.getLogger().setLevel(logging.DEBUG)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item):
    setup_filter()
    yield

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    setup_filter()
    yield

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item):
    setup_filter()
    yield



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
