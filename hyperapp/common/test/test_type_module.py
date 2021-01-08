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
    TClass,
    NotificationCmd,
    Interface,
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
    assert htypes.type_module_1.record_1.match(TRecord('record_1', {'int_field': tInt}))

    assert htypes.type_module_1.some_int is tInt

    assert htypes.type_module_1.record_1.match(TRecord('record_1', {'int_field': tInt}))
    assert htypes.type_module_1.record_2.match(TRecord('record_1', {'int_field': tInt, 'string_field': tString}))

    # object_t = resolve_1('object')
    # simple_class = resolve_1('simple_class')

    # assert simple_class.hierarchy is object_t
    # assert simple_class.match(TClass(object_t, 'simple_2'))

    # assert resolve_1('text_object').match(
    #     TClass(object_t, 'text_2', base=simple_class, fields=OrderedDict([('text', tString)])))

    some_bool_list_opt = htypes.type_module_2.some_bool_list_opt
    assert some_bool_list_opt.match(TOptional(TList(tBool)))
    assert htypes.type_module_2.record_3.match(
        TRecord('record_1', {'int_field': tInt, 'string_field': tString, 'datetime_field': tDateTime}))

    assert htypes.type_module_2.record_with_ref.match(TRecord('record_with_ref', {'ref_field': ref_t}))
    assert htypes.type_module_2.record_with_opt_ref.match(TRecord('record_with_opt_ref', {'opt_ref_field': TOptional(ref_t)}))

    # iface_a = resolve_1('test_iface_a')
    # iface_b = resolve_2('test_iface_b')
    # assert iface_b.base is iface_a
    # assert iface_b.match(Interface(['iface_b'], base=iface_a, commands=[
    #     NotificationCmd(['test_iface_b', 'keep_alive'], 'keep_alive'),
    #     ]))
