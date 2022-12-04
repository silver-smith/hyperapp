import logging
import yaml
from pathlib import Path

import pytest

from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']

TEST_DIR = Path(__file__).parent.resolve()
TEST_RESOURCES_DIR = Path(__file__).parent / 'test_resources'


@pytest.fixture
def additional_root_dirs():
    return [TEST_RESOURCES_DIR]


@pytest.fixture
def module_dir_list(default_module_dir_list):
    return [
        *default_module_dir_list,
        TEST_RESOURCES_DIR,
        ]


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
        'resource.python_module',
        'resource.list_service',
        'resource.test.test_resources.mock_identity',
        ]


@pytest.fixture
def mosaic(services):
    return services.mosaic


@pytest.fixture
def resource_registry(services):
    return services.resource_registry


@pytest.fixture
def resource_module_factory(services):
    return services.resource_module_factory


@pytest.fixture
def compare():
    def inner(resource_module, expected_fname):
        expected_yaml = TEST_DIR.joinpath(expected_fname + '.expected.yaml').read_text()
        actual_yaml = yaml.dump(resource_module.as_dict, sort_keys=False)
        Path(f'/tmp/{expected_fname}.resources.yaml').write_text(actual_yaml)
        assert actual_yaml == expected_yaml
    return inner


def test_load(resource_registry):
    servant_list = resource_registry['test_resources', 'servant_list']
    log.info("Servant list: %r", servant_list)

    list_service = resource_registry['test_resources', 'sample_list_service']
    log.info("List service: %r", list_service)


def test_set_attr(htypes, mosaic, resource_registry, resource_module_factory, compare):
    sample_module_2 = resource_registry['sample_module_2', 'sample_module_2.module']
    res_module = resource_module_factory(resource_registry, 'test_module')
    res_module['sample_servant_2'] = htypes.attribute.attribute(
        object=mosaic.put(sample_module_2),
        attr_name='sample_servant_2',
        )
    assert res_module['sample_servant_2'] == htypes.attribute.attribute(
        object=mosaic.put(sample_module_2),
        attr_name='sample_servant_2',
        )
    compare(res_module, 'test_set_attr')


def test_set_partial(htypes, mosaic, resource_registry, resource_module_factory, compare):
    sample_module_2 = resource_registry['sample_module_2', 'sample_module_2.module']
    res_module = resource_module_factory(resource_registry, 'test_module')
    attr = htypes.attribute.attribute(
        object=mosaic.put(sample_module_2),
        attr_name='sample_servant_2',
        )
    partial = htypes.partial.partial(
        function=mosaic.put(attr),
        params=tuple([
            htypes.partial.param('mosaic', mosaic.put(htypes.legacy_service.builtin_service('mosaic'))),
            htypes.partial.param('web', mosaic.put(htypes.legacy_service.builtin_service('web'))),
            ]),
        )
    res_module['sample_servant_2'] = attr
    res_module['sample_servant_2_partial'] = partial
    assert res_module['sample_servant_2_partial'] == partial
    compare(res_module, 'test_set_partial')
