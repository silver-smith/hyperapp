import os.path
from pathlib import Path

from hyperapp.common.htypes import (
    tInt,
    tString,
    tBool,
    TOptional,
    Field,
    TRecord,
    TList,
    TClass,
    tProvidedClass,
    tTypeDef,
    t_named,
    make_root_type_namespace,
    )
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.type_module import LocalTypeModuleRegistry
from hyperapp.common.builtin_types_registry import make_builtin_types_registry
from hyperapp.common.ref_registry import RefRegistry
from hyperapp.common.ref_resolver import RefResolver
from hyperapp.common.type_module_loader import TypeModuleLoader
from hyperapp.common.type_resolver import TypeResolver


TEST_MODULES_DIR = Path(__file__).parent.resolve()


def test_type_module_loader():
    types = make_root_type_namespace()
    builtin_types_registry = make_builtin_types_registry()
    local_type_module_registry = LocalTypeModuleRegistry()
    ref_registry = RefRegistry(types)
    loader = TypeModuleLoader(types.builtins, builtin_types_registry, ref_registry, local_type_module_registry)
    loader.load_type_module('test_module_1', TEST_MODULES_DIR / 'test_module_1.types')
    loader.load_type_module('test_module_2', TEST_MODULES_DIR / 'test_module_2.types')


def test_type_resolver():
    types = make_root_type_namespace()
    builtin_types_registry = make_builtin_types_registry()
    local_type_module_registry = LocalTypeModuleRegistry()
    ref_registry = RefRegistry(types)
    loader = TypeModuleLoader(types.builtins, builtin_types_registry, ref_registry, local_type_module_registry)
    loader.load_type_module('test_module_1', TEST_MODULES_DIR / 'test_module_1.types')
    loader.load_type_module('test_module_2', TEST_MODULES_DIR / 'test_module_2.types')

    ref_resolver = RefResolver(types)
    ref_resolver.add_source(ref_registry)

    type_resolver = TypeResolver(types, builtin_types_registry, ref_resolver)

    def resolve(name):
        return type_resolver.resolve(local_type_module_registry['test_module_1'][name])

    assert resolve('some_int') == tInt
    assert (resolve('record_1') == TRecord([Field('int_field', tInt)]))

    assert resolve('some_int') == tInt

    assert resolve('record_1') == TRecord([Field('int_field', tInt)])
    assert resolve('record_2') == TRecord([Field('int_field', tInt), Field('string_field', tString)])

    object_t = resolve('object')
    simple_class = resolve('simple_class')

    assert simple_class.hierarchy is object_t
    assert simple_class == TClass(object_t, 'simple_2', TRecord([]))

    assert resolve('text_object') == TClass(object_t, 'text_2', base=simple_class, trec=TRecord([Field('text', tString)]))

    some_bool_list_opt = type_resolver.resolve(local_type_module_registry['test_module_1']['some_bool_list_opt'])
    assert some_bool_list_opt == TOptional(TList(tBool))
