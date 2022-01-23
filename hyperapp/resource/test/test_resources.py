import logging
from pathlib import Path

import pytest
import yaml

from hyperapp.common.htypes import tString, TList, TRecord
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
        'resource.resource_type',
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


def test_definition_type(services, htypes, code):
    resource_t = htypes.partial.partial
    resource_type = code.resource_type.ResourceType(services.types, services.mosaic, services.web, resource_t)
    log.info("definition_t: %r", resource_type.definition_t)
    assert resource_type.definition_t == TRecord('partial', {
        'function': tString,
        'params': TList(TRecord('param', {
            'name': tString,
            'value': tString,
            })),
        })


def test_read_definition(services, htypes, code):
    resource_t = htypes.partial.partial
    resource_type = code.resource_type.ResourceType(services.types, services.mosaic, services.web, resource_t)
    log.info("definition_t: %r", resource_type.definition_t)
    definition_dict = {
        'function': 'some_function',
        'params': {
            'param_1': 'value_1',
            'param_2': 'value_2',
            },
        }
    definition = resource_type.parse(definition_dict)
    log.info("definition: %r", definition)
    param_t = resource_type.definition_t.fields['params'].element_t
    assert definition == resource_type.definition_t(
        function='some_function',
        params=[
            param_t('param_1', 'value_1'),
            param_t('param_2', 'value_2'),
            ],
        )


def test_resolve_definition(services, htypes, code):
    resource_t = htypes.partial.partial
    resource_type = code.resource_type.ResourceType(services.types, services.mosaic, services.web, resource_t)
    param_t = resource_type.definition_t.fields['params'].element_t
    definition = resource_type.definition_t(
        function='some_function',
        params=[
            param_t('param_1', 'value_1'),
            param_t('param_2', 'value_2'),
            ],
        )
    names = {
        'some_function': services.mosaic.put('some_function'),
        'value_1': services.mosaic.put(111),
        'value_2': services.mosaic.put(222),
        }

    def resolve_name(name):
        return names[name]

    resource = resource_type.resolve(definition, resolve_name)
    log.info('Resolved resource: %r', resource)
    assert resource == resource_t(
        function=names['some_function'],
        params=[
            htypes.partial.param('param_1', names['value_1']),
            htypes.partial.param('param_2', names['value_2']),
        ],
    )
