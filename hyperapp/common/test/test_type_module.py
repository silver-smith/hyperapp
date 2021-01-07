from collections import OrderedDict
import os.path
from pathlib import Path
import pytest

from hyperapp.common.htypes import (
    tInt,
    tString,
    tBool,
    TOptional,
    TRecord,
    TList,
    TClass,
    NotificationCmd,
    Interface,
    t_named,
    register_builtin_types,
    )
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.local_type_module import LocalTypeModuleRegistry
from hyperapp.common.mosaic import Mosaic
from hyperapp.common.web import Web
from hyperapp.common.type_module_loader import TypeModuleLoader
from hyperapp.common.type_system import TypeSystem


TEST_MODULES_DIR = Path(__file__).parent.resolve()



@pytest.fixture
def web():
    return Web()


@pytest.fixture
def types():
    return TypeSystem()


@pytest.fixture
def mosaic(web, types):
    mosaic = Mosaic(types)
    types.init_mosaic(mosaic)
    web.add_source(mosaic)
    register_builtin_types(types)
    return mosaic


def test_type_module_loader(types, mosaic):
    local_type_module_registry = LocalTypeModuleRegistry()
    loader = TypeModuleLoader(types, mosaic, local_type_module_registry)
    loader.load_type_module(TEST_MODULES_DIR / 'type_module_1.types')
    loader.load_type_module(TEST_MODULES_DIR / 'type_module_2.types')


def test_types(web, types, mosaic):
    local_type_module_registry = LocalTypeModuleRegistry()
    loader = TypeModuleLoader(types, mosaic, local_type_module_registry)
    loader.load_type_module(TEST_MODULES_DIR / 'type_module_1.types')
    loader.load_type_module(TEST_MODULES_DIR / 'type_module_2.types')

    def resolve_1(name):
        return types.resolve(local_type_module_registry['type_module_1'][name])

    def resolve_2(name):
        return types.resolve(local_type_module_registry['type_module_2'][name])

    assert resolve_1('some_int') is tInt
    assert (resolve_1('record_1').match(TRecord('record_1', OrderedDict([('int_field', tInt)]))))

    assert resolve_1('some_int') is tInt

    assert resolve_1('record_1').match(TRecord('record_1', OrderedDict([('int_field', tInt)])))
    assert resolve_1('record_2').match(TRecord('record_1', OrderedDict([('int_field', tInt), ('string_field', tString)])))

    object_t = resolve_1('object')
    simple_class = resolve_1('simple_class')

    assert simple_class.hierarchy is object_t
    assert simple_class.match(TClass(object_t, 'simple_2'))

    assert resolve_1('text_object').match(
        TClass(object_t, 'text_2', base=simple_class, fields=OrderedDict([('text', tString)])))

    some_bool_list_opt = resolve_2('some_bool_list_opt')
    assert some_bool_list_opt.match(TOptional(TList(tBool)))

    iface_a = resolve_1('test_iface_a')
    iface_b = resolve_2('test_iface_b')
    assert iface_b.base is iface_a
    assert iface_b.match(Interface(['iface_b'], base=iface_a, commands=[
        NotificationCmd(['test_iface_b', 'keep_alive'], 'keep_alive'),
        ]))
