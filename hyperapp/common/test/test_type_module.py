from collections import OrderedDict
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
    TList,
    Request,
    Notification,
    Interface,
    ListService,
    ref_t,
    register_builtin_types,
    )
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.local_type_module import LocalTypeModuleRegistry
from hyperapp.common.mosaic import Mosaic
from hyperapp.common.web import Web
from hyperapp.common.type_module_loader import TypeModuleLoader
from hyperapp.common.type_system import TypeSystem
from hyperapp.common.test.hyper_types_namespace import HyperTypesNamespace


TEST_MODULES_DIR = Path(__file__).parent.resolve()


@pytest.fixture
def types():
    return TypeSystem()


@pytest.fixture
def mosaic(types):
    mosaic = Mosaic(types)
    types.init_mosaic(mosaic)
    register_builtin_types(types)
    return mosaic


@pytest.fixture
def local_type_module_registry():
    return LocalTypeModuleRegistry()


@pytest.fixture
def htypes(types, local_type_module_registry):
    return HyperTypesNamespace(types, local_type_module_registry)


def test_type_module_loader(types, mosaic, local_type_module_registry):
    loader = TypeModuleLoader(types, mosaic, local_type_module_registry)
    loader.load_type_module(TEST_MODULES_DIR / 'type_module_1.types')
    loader.load_type_module(TEST_MODULES_DIR / 'type_module_2.types')


def test_types(types, mosaic, local_type_module_registry, htypes):
    loader = TypeModuleLoader(types, mosaic, local_type_module_registry)
    loader.load_type_module(TEST_MODULES_DIR / 'type_module_1.types')
    loader.load_type_module(TEST_MODULES_DIR / 'type_module_2.types')

    assert htypes.type_module_1.some_int is tInt

    assert htypes.type_module_1.some_string_opt == TOptional(tString)
    assert htypes.type_module_1.some_bool_list == TList(tBool)
    assert htypes.type_module_1.some_bool_list_opt_1 == TOptional(TList(tBool))
    assert htypes.type_module_1.some_bool_list_opt_2 == TOptional(TList(tBool))

    assert htypes.type_module_1.record_1 == TRecord('record_1', {'int_field': tInt})

    assert htypes.type_module_1.some_int is tInt

    assert htypes.type_module_1.record_1 == TRecord('record_1', {'int_field': tInt})
    assert htypes.type_module_1.record_2 == TRecord('record_2', {'int_field': tInt, 'string_field': tString})

    some_bool_list_opt = htypes.type_module_2.some_bool_list_opt
    assert some_bool_list_opt == TOptional(TList(tBool))

    assert (htypes.type_module_2.record_3 ==
            TRecord('record_3', {'int_field': tInt, 'string_field': tString, 'datetime_field': tDateTime}))

    assert htypes.type_module_2.ref_opt == TOptional(ref_t)
    assert htypes.type_module_2.ref_list_opt == TOptional(TList(ref_t))

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


def test_list_service(types, mosaic, local_type_module_registry, htypes):
    loader = TypeModuleLoader(types, mosaic, local_type_module_registry)
    loader.load_type_module(TEST_MODULES_DIR / 'list_service.types')

    field_dict = {
        'datetime_field': tDateTime,
        'string_list_field': TList(tString),
        'int_opt_field': TOptional(tInt),
        }
    assert htypes.list_service.test_list_service == ListService(
        name='test_list_service',
        field_dict=field_dict,
        interface=None,
        )
    # Types should be registered:
    types.reverse_resolve(htypes.list_service.test_list_service.interface)
    [method] = htypes.list_service.test_list_service.interface.methods.values()
    types.reverse_resolve(method.params_record_t)
    types.reverse_resolve(method.response_record_t)

    assert htypes.list_service.test_list_service.interface == Interface(
        name='test_list_service_interface',
        base=None,
        method_list=[
            Request(
                method_name='get',
                params_record_t=TRecord('test_list_service_interface_get_params'),
                response_record_t=TRecord('test_list_service_interface_get_response', {
                    'rows': TRecord('test_list_service_row', field_dict),
                    }),
                ),
            ],
        )
