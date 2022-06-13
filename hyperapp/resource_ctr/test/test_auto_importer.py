import logging
import time

import pytest

from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def code_module_list():
    return [
        'resource.resource_type',
        'resource.registry',
        'resource.resource_module',
        'resource.legacy_module',
        'resource.legacy_service',
        'resource.legacy_type',
        'resource.attribute',
        'resource.partial',
        'resource.call',
        'resource.list_service',
        'resource.live_list_service',
        'resource.tree_service',
        'resource.value',
        'resource.piece_ref',
        'resource.typed_piece',
        'resource.selector',
        'resource.rpc_command',
        'resource.rpc_callback',
        'resource.map_service',
        'resource.python_module',
        ]


def test_auto_importer(services):
    module = services.resource_module_registry['sync.subprocess_context']
    subprocess_running_res = module['subprocess_running']
    subprocess_running = services.python_object_creg.animate(subprocess_running_res)
    with subprocess_running('auto_importer') as process:
        log.info("Subprocess is running")
        time.sleep(5)
