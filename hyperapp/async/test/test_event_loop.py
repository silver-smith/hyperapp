import asyncio
import logging

import pytest

from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)

pytest_plugins = ['hyperapp.common.test.services']


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
        'async.test.module_async_init_close',
        ]


def test_event_loop(services):
    assert services.test_init_event.wait(timeout=1)
    services.stop()
    assert services.test_stop_event.wait(timeout=1)
