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
from hyperapp.common.type_module_parser import load_type_module
from hyperapp.common.type_module import LocalTypeModuleRegistry, map_type_module_to_refs, resolve_type_module
from hyperapp.common.builtin_types_registry import make_builtin_types_registry
from hyperapp.common.ref_registry import RefRegistry


TEST_TYPE_MODULES_DIR = Path(__file__).parent.resolve()


def make_fpath(module_name):
    return TEST_TYPE_MODULES_DIR / module_name


def test_load_and_resolve():
    types = make_root_type_namespace()
    module_1 = load_type_module(types.builtins, 'test_module_1', make_fpath('test_module_1.types'))
    ns = resolve_type_module(types, module_1)

    assert tInt == ns.get('some_int')

    assert ns.record_1 == TRecord([Field('int_field', tInt)])
    assert ns.record_2 == TRecord([Field('int_field', tInt), Field('string_field', tString)])

    assert 'object' in ns
    object_t = ns.object

    assert 'simple_class' in ns
    simple_class = ns.simple_class
    assert TClass(object_t, 'simple_2', TRecord([])) == simple_class

    assert 'text_object' in ns
    assert TClass(object_t, 'text_2', base=simple_class, trec=TRecord([Field('text', tString)])) == ns.text_object

    assert [] == module_1.import_list

    types[module_1.module_name] = ns
    module_2 = load_type_module(types.builtins, 'test_module_2', make_fpath('test_module_2.types'))
    assert tProvidedClass('object', 'text_object_2') in module_2.provided_classes

    ns2 = resolve_type_module(types, module_2)

    assert TOptional(TList(tBool)) == ns2.some_bool_list_opt


def test_map_to_refs():
    types = make_root_type_namespace()
    builtin_types_registry = make_builtin_types_registry()
    local_type_module_registry = LocalTypeModuleRegistry()
    ref_registry = RefRegistry(types)
    source_module_1 = load_type_module(types.builtins, 'test_module_1', make_fpath('test_module_1.types'))
    local_type_module_1 = map_type_module_to_refs(builtin_types_registry, ref_registry, local_type_module_registry, source_module_1)
    local_type_module_registry.register('test_module_1', local_type_module_1)
    source_module_2 = load_type_module(types.builtins, 'test_module_2', make_fpath('test_module_2.types'))
    local_type_module_2 = map_type_module_to_refs(builtin_types_registry, ref_registry, local_type_module_registry, source_module_2)
