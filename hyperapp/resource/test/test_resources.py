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
        'resource.resource_module',
        'resource.legacy_module',
        'resource.legacy_service',
        'resource.legacy_type',
        'resource.attribute',
        'resource.partial',
        'resource.call',
        'resource.list_service',
        'resource.value',
        ]


def test_resources(services):
    module = services.resource_module_registry['test_resources']

    servant_list = module['servant_list']
    log.info("Servant list: %r", servant_list)

    list_service = module['sample_list_service']
    log.info("List service: %r", list_service)


def test_definition_type(services, htypes, code):
    resource_t = htypes.partial.partial
    resource_type = code.resource_type.ResourceType(services.types, services.mosaic, services.web, 'partial', resource_t)
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
    resource_type = code.resource_type.ResourceType(services.types, services.mosaic, services.web, 'partial', resource_t)
    log.info("definition_t: %r", resource_type.definition_t)
    definition_dict = {
        'function': 'some_function',
        'params': {
            'param_1': 'value_1',
            'param_2': 'value_2',
            },
        }
    definition = resource_type.from_dict(definition_dict)
    log.info("definition: %r", definition)
    param_t = resource_type.definition_t.fields['params'].element_t
    assert definition == resource_type.definition_t(
        function='some_function',
        params=(
            param_t('param_1', 'value_1'),
            param_t('param_2', 'value_2'),
            ),
        )


def test_resolve_definition_partial(services, htypes, code):
    resource_t = htypes.partial.partial
    resource_type = code.resource_type.ResourceType(services.types, services.mosaic, services.web, 'partial', resource_t)
    param_t = resource_type.definition_t.fields['params'].element_t
    definition = resource_type.definition_t(
        function='some_function',
        params=(
            param_t('param_1', 'value_1'),
            param_t('param_2', 'value_2'),
            ),
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
        params=(
            htypes.partial.param('param_1', names['value_1']),
            htypes.partial.param('param_2', names['value_2']),
        ),
    )


# Inherited record result_t should also work.
def test_resolve_definition_list_service(services, htypes, code):
    resource_t = htypes.resource_service.list_service
    resource_type = code.resource_type.ResourceType(services.types, services.mosaic, services.web, 'partial', resource_t)
    definition = resource_type.definition_t(
        identity='some_identity',
        function='some_function',
        dir='some_dir',
        commands=['some_command'],
        key_attribute='the_key',
        )
    names = {
        'some_identity': services.mosaic.put('some_identity'),
        'some_function': services.mosaic.put('some_function'),
        'some_dir': services.mosaic.put('some_dir'),
        'some_command': services.mosaic.put('some_command'),
        }

    def resolve_name(name):
        return names[name]

    resource = resource_type.resolve(definition, resolve_name)
    log.info('Resolved resource: %r', resource)
    assert resource == resource_t(
        identity=names['some_identity'],
        function=names['some_function'],
        dir=names['some_dir'],
        commands=(names['some_command'],),
        key_attribute='the_key',
        )


def test_value_type(services, htypes, code):
    t = code.value.ValueResourceType(services.mosaic, services.types)
    data = {
        'value': ['item_1', 'item_2'],
        }

    definition = t.from_dict(data)
    value = ('item_1', 'item_2')
    assert definition == htypes.value.value(
        value_ref=services.mosaic.put(value),
        )

    resource = t.resolve(definition, lambda name: None)
    assert resource == definition

    assert services.python_object_creg.animate(resource) == value
