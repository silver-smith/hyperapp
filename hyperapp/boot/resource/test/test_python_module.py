import logging
import yaml
from pathlib import Path

import pytest

from hyperapp.boot.htypes.python_module import python_module_t, python_module_def_t, import_rec_t, import_rec_def_t
from hyperapp.boot.resource.python_module import PythonModuleResourceType
from hyperapp.boot import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = [
    'hyperapp.boot.test.services',
    ]

TEST_DIR = Path(__file__).parent.resolve()
TEST_RESOURCES_DIR = TEST_DIR / 'test_resources'


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
def resource_type_reg():
    reg = {}
    reg[python_module_t] = PythonModuleResourceType()
    return reg


def test_definition_type(resource_type_producer):
    resource_t = python_module_t
    resource_type = resource_type_producer(resource_t)
    assert resource_type.definition_t is python_module_def_t


def test_from_dict(resource_type_producer):
    resource_t = python_module_t
    resource_type = resource_type_producer(resource_t)
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
            import_rec_def_t('some.used_1', 'some.resource_1'),
            ),
        )


def test_resolve(mosaic, resource_type_producer):
    resource_t = python_module_t
    resource_type = resource_type_producer(resource_t)

    names = {
        'resource_1': mosaic.put('resource 1'),
        'resource_2': mosaic.put('resource 2'),
        }
    def resolve_name(name):
        return names[name]

    definition = resource_type.definition_t(
        module_name='sample module',
        file_name='sample_module.dyn.py',
        import_list=(
            import_rec_def_t('some.used_1', 'resource_1'),
            import_rec_def_t('some.used_2', 'resource_2'),
            ),
        )

    resource = resource_type.resolve(definition, resolve_name, TEST_RESOURCES_DIR)
    log.info('Resolved resource: %r', resource)

    assert resource == resource_t(
        module_name='sample module',
        source=TEST_RESOURCES_DIR.joinpath('sample_module.dyn.py').read_text(),
        file_path=str(TEST_RESOURCES_DIR / 'sample_module.dyn.py'),
        import_list=(
            import_rec_t('some.used_1', names['resource_1']),
            import_rec_t('some.used_2', names['resource_2']),
            ),
        )


def test_reverse_resolve(mosaic, resource_type_producer):
    resource_t = python_module_t
    resource_type = resource_type_producer(resource_t)

    names = {
        'resource_1': mosaic.put('resource 1'),
        'resource_2': mosaic.put('resource 2'),
        }
    reverse_names = {
        value: key for key, value in names.items()
        }
    def reverse_resolve_name(name):
        return reverse_names[name]

    resource = resource_t(
        module_name='sample module',
        source=TEST_RESOURCES_DIR.joinpath('sample_module.dyn.py').read_text(),
        file_path=str(TEST_RESOURCES_DIR / 'sample_module.dyn.py'),
        import_list=(
            import_rec_t('some.used_1', names['resource_1']),
            import_rec_t('some.used_2', names['resource_2']),
            ),
        )

    definition = resource_type.reverse_resolve(resource, reverse_resolve_name, TEST_RESOURCES_DIR)
    log.info('Resolved definition: %r', definition)

    assert definition == resource_type.definition_t(
        module_name='sample module',
        file_name='sample_module.dyn.py',
        import_list=(
            import_rec_def_t('some.used_1', 'resource_1'),
            import_rec_def_t('some.used_2', 'resource_2'),
            ),
        )


def test_python_module_resource(resource_registry, pyobj_creg):
    python_module_resource = resource_registry['sample_python_module', 'sample_python_module']
    log.info("Loading python module: %r", python_module_resource)
    python_module = pyobj_creg.animate(python_module_resource)
    log.info("Python module: %r", python_module)
    assert python_module.value.key == 123


def test_fixture(resource_registry, pyobj_creg):
    fixture = resource_registry['sample_fixture.fixtures', 'sample_fixture']
    log.info("Sample fixture: %r", fixture)
    python_module = pyobj_creg.animate(fixture)
    log.info("Python module: %r", python_module)
    log.info("Sample item: %r", python_module.sample_item)
