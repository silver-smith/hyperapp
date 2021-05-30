import asyncio
import logging
from pathlib import Path

import pytest

from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)

pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def additional_code_module_dirs():
    return [Path(__file__).parent]


@pytest.fixture(params=['native', 'qt'])
def event_loop_module(request):
    if request.param == 'native':
        return 'async.event_loop'
    if request.param == 'qt':
        return 'async.ui.qt.application'
    assert False, request.param


@pytest.fixture
def code_module_list(event_loop_module):
    return [
        event_loop_module,
        'async.async_main',
        'module_async_init_close',
        ]


@pytest.fixture
def post_stop_checks():
    def check(services):
        assert services.test_stop_event.wait(timeout=1)
    return check


def test_event_loop(services):
    assert services.test_init_event.wait(timeout=1)
    services.stop_signal.set()
