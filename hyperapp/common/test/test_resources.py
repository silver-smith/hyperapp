import logging
from pathlib import Path

import pytest
import yaml

from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']

TEST_DIR = Path(__file__).parent.resolve()


@pytest.fixture
def code_module_list():
    return [
        'common.resource_registry',
        'common.resource.legacy_module',
        'common.resource.legacy_service',
        'common.resource.factory',
        'common.resource.call',
        ]


def test_resources(services):
    resource_type_registry = services.resource_type_registry
    resources = yaml.safe_load(TEST_DIR.joinpath('test_resources.resources.yaml').read_text())
    name_to_resource = services.resource_registry.load_definitions(resources)
    servant_list_ref = name_to_resource['servant_list']
    servant_list = services.python_object_creg.invite(servant_list_ref)
    log.info("Servant list: %r", servant_list)
