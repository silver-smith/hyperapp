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
from hyperapp.common.type_module import map_type_module_to_refs, resolve_type_module
from hyperapp.common.ref_registry import RefRegistry


TEST_TYPE_MODULES_DIR = Path(__file__).parent.resolve()


def make_fpath(module_name):
    return TEST_TYPE_MODULES_DIR / module_name


def test_load_and_resolve():
    types = make_root_type_namespace()
    module = load_type_module(types.builtins, 'test_module1', make_fpath('test_module1.types'))
    ns = resolve_type_module(types, module)

    assert tInt == ns.get('some_int')

    assert ns.record1 == TRecord([Field('int_field', tInt)])
    assert ns.record2 == TRecord([Field('int_field', tInt), Field('string_field', tString)])

    assert 'object' in ns
    object_t = ns.object

    assert 'simple_class' in ns
    simple_class = ns.simple_class
    assert TClass(object_t, 'simple_2', TRecord([])) == simple_class

    assert 'text_object' in ns
    assert TClass(object_t, 'text_2', base=simple_class, trec=TRecord([Field('text', tString)])) == ns.text_object

    assert [] == module.import_list

    types[module.module_name] = ns
    module2 = load_type_module(types.builtins, 'test_module2', make_fpath('test_module2.types'))
    assert tProvidedClass('object', 'text_object_2') in module2.provided_classes

    ns2 = resolve_type_module(types, module2)

    assert TOptional(TList(tBool)) == ns2.some_bool_list_opt


def test_map_to_refs():
    types = make_root_type_namespace()
    ref_registry = RefRegistry(types)
    source_module_1 = load_type_module(types.builtins, 'test_module1', make_fpath('test_module1.types'))
    name_registry_1 = dict(map_type_module_to_refs(types, ref_registry, source_module_1))
    source_module_2 = load_type_module(types.builtins, 'test_module2', make_fpath('test_module2.types'))
#    name_registry_2 = dict(map_type_module_to_refs(types, ref_registry, source_module_1))
