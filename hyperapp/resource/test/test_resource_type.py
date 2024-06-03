import logging
from pathlib import Path

import pytest

from hyperapp.common.htypes import tString, TOptional, TList, TRecord
from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


TEST_RESOURCES_DIR = Path(__file__).parent / 'test_resources'


@pytest.fixture
def module_dir_list(default_module_dir_list):
    return [
        *default_module_dir_list,
        TEST_RESOURCES_DIR,
        ]


def test_definition_type_partial(resource_type_factory, htypes):
    resource_t = htypes.partial.partial
    resource_type = resource_type_factory(resource_t)
    log.info("definition_t: %r", resource_type.definition_t)
    assert resource_type.definition_t == TRecord('partial', 'partial_def', {
        'function': tString,
        'params': TList(TRecord('partial', 'param_def', {
            'name': tString,
            'value': tString,
            })),
        })


def test_definition_type_based(resource_type_factory, htypes):
    resource_t = htypes.test_resources.test_resource_t
    resource_type = resource_type_factory(resource_t)
    log.info("definition_t: %r", resource_type.definition_t)
    expected_base_t = TRecord('test_resources', 'test_resource_t_base_def', {
        'value': TOptional(tString),
        })
    assert resource_type.definition_t == TRecord('test_resources', 'test_resource_t_def', {
        'value': TOptional(tString),
        'other_value': TList(tString),
        }, base=expected_base_t)


def test_mapper(resource_type_factory, htypes):
    resource_t = htypes.partial.partial
    resource_type = resource_type_factory(resource_t)
    log.info("mapper: %r", resource_type._mapper)


def test_from_dict_partial(resource_type_factory, htypes):
    resource_t = htypes.partial.partial
    resource_type = resource_type_factory(resource_t)
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


def test_from_dict_based(resource_type_factory, htypes):
    resource_t = htypes.test_resources.test_resource_t
    resource_type = resource_type_factory(resource_t)
    log.info("definition_t: %r", resource_type.definition_t)
    definition_dict = {
        'value': 'some value',
        'other_value': ['some other value 1', 'some other value 2'],
        }
    definition = resource_type.from_dict(definition_dict)
    log.info("definition: %r", definition)
    assert definition == resource_type.definition_t(
        value='some value',
        other_value=('some other value 1', 'some other value 2'),
        )


def test_to_dict_partial(resource_type_factory, htypes):
    resource_t = htypes.partial.partial
    resource_type = resource_type_factory(resource_t)
    param_t = resource_type.definition_t.fields['params'].element_t
    definition = resource_type.definition_t(
        function='some_function',
        params=(
            param_t('param_1', 'value_1'),
            param_t('param_2', 'value_2'),
            ),
        )
    definition_dict = resource_type.to_dict(definition)
    log.info("definition dict: %r", definition_dict)
    assert definition_dict == {
        'function': 'some_function',
        'params': {
            'param_1': 'value_1',
            'param_2': 'value_2',
            },
        }


def test_to_dict_based(resource_type_factory, htypes):
    resource_t = htypes.test_resources.test_resource_t
    resource_type = resource_type_factory(resource_t)
    definition = resource_type.definition_t(
        value='some value',
        other_value=('some other value 1', 'some other value 2'),
        )
    definition_dict = resource_type.to_dict(definition)
    log.info("definition dict: %r", definition_dict)
    assert definition_dict == {
        'value': 'some value',
        'other_value': ['some other value 1', 'some other value 2'],
        }


def test_resolve_definition_partial(mosaic, resource_type_factory, htypes):
    resource_t = htypes.partial.partial
    resource_type = resource_type_factory(resource_t)
    param_t = resource_type.definition_t.fields['params'].element_t
    definition = resource_type.definition_t(
        function='some_function',
        params=(
            param_t('param_1', 'value_1'),
            param_t('param_2', 'value_2'),
            ),
        )
    names = {
        'some_function': mosaic.put('some_function'),
        'value_1': mosaic.put(111),
        'value_2': mosaic.put(222),
        }

    def resolve_name(name):
        return names[name]

    resource = resource_type.resolve(definition, resolve_name, TEST_RESOURCES_DIR)
    log.info('Resolved resource: %r', resource)
    assert resource == resource_t(
        function=names['some_function'],
        params=(
            htypes.partial.param('param_1', names['value_1']),
            htypes.partial.param('param_2', names['value_2']),
        ),
    )


def test_resolve_definition_based(mosaic, resource_type_factory, htypes):
    resource_t = htypes.test_resources.test_resource_t
    resource_type = resource_type_factory(resource_t)
    definition = resource_type.definition_t(
        value='some-value',
        other_value=('other-1', 'other-2'),
        )
    names = {
        'some-value': mosaic.put('some value'),
        'other-1': mosaic.put(111),
        'other-2': mosaic.put(222),
        }

    def resolve_name(name):
        return names[name]

    resource = resource_type.resolve(definition, resolve_name, TEST_RESOURCES_DIR)
    log.info('Resolved resource: %r', resource)
    assert resource == resource_t(
        value=names['some-value'],
        other_value=(names['other-1'], names['other-2']),
    )


def test_reverse_resolve_definition_partial(mosaic, resource_type_factory, htypes):
    resource_t = htypes.partial.partial
    resource_type = resource_type_factory(resource_t)
    names = {
        'some_function': mosaic.put('some_function'),
        'value_1': mosaic.put(111),
        'value_2': mosaic.put(222),
        }
    reverse_names = {
        value: key for key, value in names.items()
        }
    resource = resource_t(
        function=names['some_function'],
        params=(
            htypes.partial.param('param_1', names['value_1']),
            htypes.partial.param('param_2', names['value_2']),
            ),
        )

    def reverse_resolve_name(name):
        return reverse_names[name]

    definition = resource_type.reverse_resolve(resource, reverse_resolve_name, TEST_RESOURCES_DIR)
    log.info('Resolved definition: %r', definition)
    param_t = resource_type.definition_t.fields['params'].element_t
    assert definition == resource_type.definition_t(
        function='some_function',
        params=(
            param_t('param_1', 'value_1'),
            param_t('param_2', 'value_2'),
        ),
    )


def test_reverse_resolve_definition_based(mosaic, resource_type_factory, htypes):
    resource_t = htypes.test_resources.test_resource_t
    resource_type = resource_type_factory(resource_t)
    names = {
        'some-value': mosaic.put('some value'),
        'other-1': mosaic.put(111),
        'other-2': mosaic.put(222),
        }
    reverse_names = {
        value: key for key, value in names.items()
        }
    resource = resource_t(
        value=names['some-value'],
        other_value=(names['other-1'], names['other-2']),
        )

    def reverse_resolve_name(name):
        return reverse_names[name]

    definition = resource_type.reverse_resolve(resource, reverse_resolve_name, TEST_RESOURCES_DIR)
    log.info('Resolved definition: %r', definition)
    assert definition == resource_type.definition_t(
        value='some-value',
        other_value=('other-1', 'other-2'),
        )


# Inherited record result_t should also work.
def test_resolve_definition_list_service(mosaic, resource_type_factory, htypes):
    resource_t = htypes.resource_service.list_service
    resource_type = resource_type_factory(resource_t)
    definition = resource_type.definition_t(
        identity='some_identity',
        function='some_function',
        dir='some_dir',
        commands=['some_command'],
        key_attribute='the_key',
        )
    names = {
        'some_identity': mosaic.put('some_identity'),
        'some_function': mosaic.put('some_function'),
        'some_dir': mosaic.put('some_dir'),
        'some_command': mosaic.put('some_command'),
        }

    def resolve_name(name):
        return names[name]

    resource = resource_type.resolve(definition, resolve_name, TEST_RESOURCES_DIR)
    log.info('Resolved resource: %r', resource)
    assert resource == resource_t(
        identity=names['some_identity'],
        function=names['some_function'],
        dir=names['some_dir'],
        commands=(names['some_command'],),
        key_attribute='the_key',
        )
