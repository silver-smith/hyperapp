import logging
from pathlib import Path

import pytest
import yaml

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
        'resource.registry',
        'resource.legacy_module',
        'resource.legacy_service',
        'resource.legacy_type',
        'resource.attribute',
        'resource.partial',
        'resource.call',
        'resource.list_service',
        'resource.resource_module',
        ]


def test_resources(services):
    module = services.resource_module_registry['resource.test.test_resources']
    servant_list = module.make('servant_list')
    log.info("Servant list: %r", servant_list)

    list_service = module.make('sample_list_service')
    log.info("List service: %r", list_service)
