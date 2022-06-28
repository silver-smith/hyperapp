import asyncio
import logging
from pathlib import Path

import pytest

from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)

pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def module_dir_list(default_module_dir_list):
    return [
        *default_module_dir_list,
        Path(__file__).parent,
        ]


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
        'async.test.module_async_init_close',
        ]


@pytest.fixture
def post_stop_checks():
    def check(services):
        assert services.test_stop_event.wait(timeout=1)
    return check


def test_event_loop(services):
    assert services.test_init_event.wait(timeout=1)
    services.stop_signal.set()
