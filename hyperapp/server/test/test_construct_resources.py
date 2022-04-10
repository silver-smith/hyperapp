import logging
import yaml
from pathlib import Path

import pytest

from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']

TEST_DIR = Path(__file__).parent.resolve()
HYPERAPP_DIR = TEST_DIR.parent.parent
TEST_RESOURCE_DIR = TEST_DIR / 'test_resources'


@pytest.fixture
def additional_module_dirs():
    return [TEST_RESOURCE_DIR, HYPERAPP_DIR / 'common' / 'test' / 'mock']


@pytest.fixture
def code_module_list():
    return [
        'mock_file_bundle',
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


def test_fixture(services):
    module = services.fixture_resource_module_registry['construct_resources_sample']
    fixture = module['construct_resources_sample']
    log.info("Sample fixture: %r", fixture)
    python_module = services.python_object_creg.animate(fixture)
    log.info("Python module: %r", python_module)


@pytest.fixture
def compare():
    def inner(resource_module, expected_fname):
        expected_yaml = TEST_RESOURCE_DIR.joinpath(expected_fname + '.resources.yaml').read_text()
        actual_yaml = yaml.dump(resource_module.as_dict, sort_keys=False)
        assert expected_yaml == actual_yaml
    return inner


def test_resources(services, compare):
    htest_module = services.resource_module_registry['server.htest']
    htest_resource = htest_module['htest']
    htest = services.python_object_creg.animate(htest_resource)
    log.info("Htest: %r", htest)
    resource_module = htest.construct_resources('construct_resources_sample', TEST_RESOURCE_DIR)
    log.info("Resource module:\n%s", yaml.dump(resource_module.as_dict, sort_keys=False))
    compare(resource_module, 'reference')
    # resource_module.save()
    servant_res = resource_module['sample_servant']
    servant = services.python_object_creg.animate(servant_res)
    log.info("Servant: %r", servant)
