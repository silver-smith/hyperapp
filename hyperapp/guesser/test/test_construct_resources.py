import logging
import tempfile
import yaml
from pathlib import Path

import pytest

from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']

TEST_DIR = Path(__file__).parent.resolve()
HYPERAPP_DIR = TEST_DIR.parent.parent
TEST_RESOURCES_DIR = TEST_DIR / 'test_resources'


@pytest.fixture
def module_dir_list(hyperapp_dir, default_module_dir_list):
    return [
        *default_module_dir_list,
        hyperapp_dir / 'guesser',
        TEST_RESOURCES_DIR,
        ]


@pytest.fixture
def code_module_list():
    return [
        'common.lcs',
        'common.lcs_service',
        'ui.impl_registry',
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
        'ui.global_command_list',
        ]


@pytest.fixture
def compare():
    def inner(resource_module, expected_fname):
        expected_yaml = TEST_RESOURCES_DIR.joinpath(expected_fname + '.expected.yaml').read_text()
        actual_yaml = yaml.dump(resource_module.as_dict, sort_keys=False)
        assert actual_yaml == expected_yaml
    return inner


def test_resources(services, htypes, hyperapp_dir, compare):
    construct_resource_res = services.resource_module_registry['guesser.construct_resources']['construct_resources']
    construct_resources = services.python_object_creg.animate(construct_resource_res)
    log.info("construct_resources: %r", construct_resources)

    resource_module = construct_resources(
        root_dir=TEST_RESOURCES_DIR,
        resource_dir_list=[],
        full_module_name='construct_resources_sample',
        module_name='construct_resources_sample',
        module_path=TEST_RESOURCES_DIR.joinpath('construct_resources_sample.dyn.py'),
        )
    log.info("Resource module:\n%s", yaml.dump(resource_module.as_dict, sort_keys=False))
    resource_module.save_as(Path(tempfile.gettempdir()) / 'construct_resources_sample.resources.yaml')
    compare(resource_module, 'construct_resources_sample')

    fn_res = resource_module['SampleServant']
    fn = services.python_object_creg.animate(fn_res)
    log.info("Constructor fn: %r", fn)

    spec_res = resource_module['sample_servant_spec']
    log.info("Servant spec resource: %r", spec_res)

    for assoc in resource_module.associations:
        services.meta_registry.animate(assoc)

    ctr_fn, spec = services.impl_registry[htypes.construct_resources_sample.sample]
    assert isinstance(spec, htypes.impl.list_spec)
