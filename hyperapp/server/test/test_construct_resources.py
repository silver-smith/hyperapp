import logging
from pathlib import Path

import pytest

from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']

TEST_DIR = Path(__file__).parent.resolve()


@pytest.fixture
def additional_module_dirs():
    return [Path(__file__).parent / 'test_resources']


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
        ]


def test_resources(services):
    htest_module = services.resource_module_registry['server.htest']
    htest_resource = htest_module['htest']
    htest = services.python_object_creg.animate(htest_resource)
    log.info("Htest: %r", htest)
    import_set, resource_dict = htest.construct_resources('construct_resources_sample')
    for import_name in sorted(import_set):
        log.info("Import: %s", import_name)
    for name, resource in resource_dict.items():
        log.info("Resource %s: %r", name, resource)
