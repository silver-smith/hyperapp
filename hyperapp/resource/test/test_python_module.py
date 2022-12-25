import logging
import yaml
from pathlib import Path

import pytest

from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']

TEST_DIR = Path(__file__).parent.resolve()
TEST_RESOURCE_DIR = TEST_DIR / 'test_resources'



@pytest.fixture
def additional_root_dirs():
    return [TEST_RESOURCE_DIR]


@pytest.fixture
def module_dir_list(default_module_dir_list):
    return [
        *default_module_dir_list,
        TEST_RESOURCE_DIR,
        ]


@pytest.fixture
def code_module_list():
    return [
        'resource.resource_type',
        'resource.registry',
        'resource.resource_module',
        'resource.legacy_type',
        'resource.python_module',
        ]


def test_definition_type(htypes, services):
    resource_t = htypes.python_module.python_module
    resource_type = services.resource_type_producer(resource_t)
    assert resource_type.definition_t is htypes.python_module.python_module_def


def test_from_dict(htypes, services):
    resource_t = htypes.python_module.python_module
    resource_type = services.resource_type_producer(resource_t)
    definition_dict = {
        'module_name': 'sample module',
        'file_name': 'sample_module.dyn.py',
        'import_list': [
            {'full_name': 'some.used_1', 'resource': 'some.resource_1'},
            ],
        }
    definition = resource_type.from_dict(definition_dict)
    log.info("definition: %r", definition)
    assert definition == resource_type.definition_t(
        module_name='sample module',
        file_name='sample_module.dyn.py',
        import_list=(
            htypes.python_module.import_rec_def('some.used_1', 'some.resource_1'),
            ),
        )


def test_resolve(htypes, services):
    resource_t = htypes.python_module.python_module
    resource_type = services.resource_type_producer(resource_t)

    names = {
        'resource_1': services.mosaic.put('resource 1'),
        'resource_2': services.mosaic.put('resource 2'),
        }
    def resolve_name(name):
        return names[name]

    definition = resource_type.definition_t(
        module_name='sample module',
        file_name='sample_module.dyn.py',
        import_list=(
            htypes.python_module.import_rec_def('some.used_1', 'resource_1'),
            htypes.python_module.import_rec_def('some.used_2', 'resource_2'),
            ),
        )

    resource = resource_type.resolve(definition, resolve_name, TEST_RESOURCE_DIR)
    log.info('Resolved resource: %r', resource)

    assert resource == resource_t(
        module_name='sample module',
        source=TEST_RESOURCE_DIR.joinpath('sample_module.dyn.py').read_text(),
        file_path=str(TEST_RESOURCE_DIR / 'sample_module.dyn.py'),
        import_list=(
            htypes.python_module.import_rec('some.used_1', names['resource_1']),
            htypes.python_module.import_rec('some.used_2', names['resource_2']),
            ),
        )


def test_reverse_resolve(htypes, services):
    resource_t = htypes.python_module.python_module
    resource_type = services.resource_type_producer(resource_t)

    names = {
        'resource_1': services.mosaic.put('resource 1'),
        'resource_2': services.mosaic.put('resource 2'),
        }
    reverse_names = {
        value: key for key, value in names.items()
        }
    def reverse_resolve_name(name):
        return reverse_names[name]

    resource = resource_t(
        module_name='sample module',
        source=TEST_RESOURCE_DIR.joinpath('sample_module.dyn.py').read_text(),
        file_path=str(TEST_RESOURCE_DIR / 'sample_module.dyn.py'),
        import_list=(
            htypes.python_module.import_rec('some.used_1', names['resource_1']),
            htypes.python_module.import_rec('some.used_2', names['resource_2']),
            ),
        )

    definition = resource_type.reverse_resolve(resource, reverse_resolve_name, TEST_RESOURCE_DIR)
    log.info('Resolved definition: %r', definition)

    assert definition == resource_type.definition_t(
        module_name='sample module',
        file_name='sample_module.dyn.py',
        import_list=(
            htypes.python_module.import_rec_def('some.used_1', 'resource_1'),
            htypes.python_module.import_rec_def('some.used_2', 'resource_2'),
            ),
        )


def test_python_module_resource(services):
    python_module_resource = services.resource_registry['sample_python_module', 'sample_python_module']
    log.info("Loading python module: %r", python_module_resource)
    python_module = services.python_object_creg.animate(python_module_resource)
    log.info("Python module: %r", python_module)
    assert python_module.value.key == 123


def test_fixture(services):
    fixture = services.resource_registry['sample_fixture.fixtures', 'sample_fixture']
    log.info("Sample fixture: %r", fixture)
    python_module = services.python_object_creg.animate(fixture)
    log.info("Python module: %r", python_module)
    log.info("Sample item: %r", python_module.sample_item)
