import logging
import yaml
from pathlib import Path

import pytest

from hyperapp.common.htypes.attribute import attribute_t
from hyperapp.common.htypes.builtin_service import builtin_service_t
from hyperapp.common.association_registry import Association
from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = [
    'hyperapp.common.test.services',
    ]

TEST_DIR = Path(__file__).parent.resolve()
TEST_RESOURCES_DIR = Path(__file__).parent / 'test_resources'


@pytest.fixture
def module_dir_list(default_module_dir_list):
    return [
        *default_module_dir_list,
        TEST_RESOURCES_DIR,
        ]


@pytest.fixture
def additional_resource_dirs():
    return [TEST_RESOURCES_DIR]


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


def test_set_attr(mosaic, resource_registry, resource_module_factory, compare):
    sample_module_2 = resource_registry['sample_module_2', 'sample_module_2.module']
    res_module = resource_module_factory(resource_registry, 'test_module')
    res_module['sample_servant_2'] = attribute_t(
        object=mosaic.put(sample_module_2),
        attr_name='sample_servant_2',
        )
    assert res_module['sample_servant_2'] == attribute_t(
        object=mosaic.put(sample_module_2),
        attr_name='sample_servant_2',
        )
    compare(res_module, 'test_set_attr')


def test_set_partial(htypes, mosaic, resource_registry, resource_module_factory, compare):
    sample_module_2 = resource_registry['sample_module_2', 'sample_module_2.module']
    res_module = resource_module_factory(resource_registry, 'test_module')
    attr = attribute_t(
        object=mosaic.put(sample_module_2),
        attr_name='sample_servant_2',
        )
    partial = htypes.partial.partial(
        function=mosaic.put(attr),
        params=tuple([
            htypes.partial.param('mosaic', mosaic.put(builtin_service_t('mosaic'))),
            htypes.partial.param('web', mosaic.put(builtin_service_t('web'))),
            ]),
        )
    res_module['sample_servant_2'] = attr
    res_module['sample_servant_2_partial'] = partial
    assert res_module['sample_servant_2_partial'] == partial
    compare(res_module, 'test_set_partial')


def test_add_association(mosaic, resource_registry, resource_module_factory, compare):
    sample_module_2 = resource_registry['sample_module_2', 'sample_module_2.module']
    key = attribute_t(
        object=mosaic.put(sample_module_2),
        attr_name='sample_key_attr',
    )
    value = attribute_t(
        object=mosaic.put(sample_module_2),
        attr_name='sample_value_attr',
    )
    ass = Association(
        bases=[key],
        key=key,
        value=value,
        )
    res_module = resource_module_factory(resource_registry, 'test_module')
    res_module['sample_key'] = key
    res_module['sample_value'] = value
    res_module.add_association(ass)
    compare(res_module, 'test_add_association')


def test_primitive(mosaic, resource_registry, resource_module_factory, compare):
    res_module = resource_module_factory(resource_registry, 'test_module')
    res_module['sample_string'] = 'abcd efgh'
    res_module['sample_int'] = 12345
    compare(res_module, 'test_primitive')
    assert res_module['sample_int'] == 12345
    assert res_module['sample_string'] == 'abcd efgh'
