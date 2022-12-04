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
