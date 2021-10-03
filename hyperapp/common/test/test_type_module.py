import os.path
from pathlib import Path
import pytest

from hyperapp.common.htypes import (
    tInt,
    tString,
    tBool,
    tDateTime,
    TOptional,
    TRecord,
    TException,
    TList,
    Request,
    Notification,
    Interface,
    ref_t,
    )
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.type_module_loader import CircularDepError, TypeModuleLoader
from hyperapp.common.test.hyper_types_namespace import HyperTypesNamespace


pytest_plugins = ['hyperapp.common.htypes.test.fixtures']


TEST_MODULES_DIR = Path(__file__).parent.resolve()


@pytest.fixture
def loader(builtin_types, mosaic, types):
    return TypeModuleLoader(builtin_types, mosaic, types)


@pytest.fixture
def htypes(types, loader):
    return HyperTypesNamespace(types, loader.registry)


def test_type_module_loader(loader):
    loader.load_type_modules(TEST_MODULES_DIR / 'test_type_modules')


def test_circular_type_dep(loader):
    with pytest.raises(CircularDepError) as excinfo:
        loader.load_type_modules(TEST_MODULES_DIR / 'circular_type_dep')
    assert str(excinfo.value) == 'Circular type module dependency: module_1->module_2->module_3->module_1'


def test_types(types, htypes, loader):
    loader.load_type_modules(TEST_MODULES_DIR / 'test_type_modules')


    assert htypes.type_module_1.record_1 == TRecord('record_1', {'int_field': tInt})
    assert htypes.type_module_1.record_2 == TRecord('record_2', {'int_field': tInt, 'string_field': tString})

    assert (htypes.type_module_2.record_3 ==
            TRecord('record_3', {'int_field': tInt, 'string_field': tString, 'datetime_field': tDateTime}))
    assert htypes.type_module_2.record_with_ref == TRecord('record_with_ref', {'ref_field': ref_t})
    assert htypes.type_module_2.record_with_opt_ref == TRecord('record_with_opt_ref', {'opt_ref_field': TOptional(ref_t)})

    assert htypes.type_module_1.empty_record_1.name == 'empty_record_1'
    assert htypes.type_module_2.empty_record_2.name == 'empty_record_2'
    assert htypes.type_module_1.empty_record_1 != htypes.type_module_2.empty_record_2


    assert htypes.type_module_1.iface_a == Interface(
        name='iface_a',
        method_list=[
            Request(
                method_name='submit',
                params_record_t=TRecord('iface_a_submit_params', {
                    'name': TList(tString),
                    'size': tInt,
                }),
                response_record_t=TRecord('iface_a_submit_response'),
                ),
            ],
        )

    assert htypes.type_module_1.iface_b == Interface(
        name='iface_b',
        base=htypes.type_module_1.iface_a,
        method_list=[
            Request(
                method_name='update',
                params_record_t=TRecord('iface_b_update_params'),
                response_record_t=TRecord('iface_b_update_response', {
                    'created_at': tDateTime,
                    'id': TOptional(tInt),
                    }),
                ),
            ],
        )

    assert htypes.type_module_2.iface_c == Interface(
        name='iface_c',
        base=htypes.type_module_1.iface_b,
        method_list=[
            Notification(
                method_name='keep_alive',
                params_record_t=TRecord('iface_c_keep_alive_params'),
                ),
            ],
        )

    # Types should be registered:
    types.reverse_resolve(htypes.type_module_1.iface_a)
    types.reverse_resolve(htypes.type_module_1.iface_a.methods['submit'].params_record_t)
    types.reverse_resolve(htypes.type_module_1.iface_a.methods['submit'].response_record_t)
    types.reverse_resolve(htypes.type_module_2.iface_c.methods['keep_alive'].params_record_t)


def test_same_instance(htypes, loader):
    loader.load_type_modules(TEST_MODULES_DIR / 'same_instance')
    element = htypes.same_instance.element('abcd')

    # Same types should resolve to same instances.
    assert htypes.same_instance.container.fields['element_field'] == htypes.same_instance.element
    assert htypes.same_instance.container.fields['element_field'] is htypes.same_instance.element
    # To be able to pass isinstance check on instantiation.
    value = htypes.same_instance.container(element_field=element)

    assert htypes.same_instance.list_container.fields['element_field'].element_t is htypes.same_instance.element
    value = htypes.same_instance.list_container(element_field=[element])

    assert htypes.same_instance.opt_container.fields['element_field'].base_t is htypes.same_instance.element
    value = htypes.same_instance.opt_container(element_field=element)

    assert htypes.same_instance.based_container.base is htypes.same_instance.container
    value = htypes.same_instance.based_container(element_field=element)
    assert isinstance(value, htypes.same_instance.container)

    assert htypes.same_instance.derived_interface.base_t is htypes.same_instance.base_interface


def test_exception_type(types, htypes, loader):
    loader.load_type_modules(TEST_MODULES_DIR / 'test_type_modules')

    assert htypes.exceptions.exception_1 == TException('exception_1', {'int_field': tInt})
    assert htypes.exceptions.exception_2 == TException('exception_2', {'int_field': tInt, 'string_field': tString})
    assert htypes.exceptions.empty_exception == TException('empty_exception', {})
