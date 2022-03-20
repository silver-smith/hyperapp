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
def additional_module_dirs():
    return [TEST_RESOURCE_DIR]


@pytest.fixture
def code_module_list():
    return [
        'resource.resource_type',
        'resource.registry',
        'resource.resource_module',
        'resource.legacy_type',
        'resource.python_module',
        'resource.fixtures',
        ]


def test_fixture(services):
    fixtures_module = services.resource_module_registry['fixtures']
    fixture = fixtures_module['construct_resources_sample']
    log.info("Sample fixture: %r", fixture)
    python_module = services.python_object_creg.animate(fixture)
    log.info("Python module: %r", python_module)
