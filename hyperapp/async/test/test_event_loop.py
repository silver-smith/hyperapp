import asyncio
import logging

import pytest

from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)

pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def code_module_list():
    return [
        'async.event_loop',
        'async.async_main',
        'async.test.module_async_init_close',
        ]


def test_native_event_loop(services):
    assert services.test_init_event.wait(timeout=1)
    services.stop()
    assert services.test_stop_event.wait(timeout=1)
