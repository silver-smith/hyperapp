import os.path
import unittest
from hyperapp.common.htypes import (
    tInt,
    tString,
    Field,
    TRecord,
    TList,
    TClass,
    tObject,
    tBaseObject,
    tTypeDef,
    t_named,
    make_meta_type_registry,
    builtin_type_registry,
    )
from hyperapp.common.visual_rep import pprint
from hyperapp.common.type_module import (
    resolve_typedefs_from_yaml_file,
    load_types_file,
    resolve_typedefs,
    )


class TypeModuleTest(unittest.TestCase):

    def setUp( self ):
        self.meta_type_registry = make_meta_type_registry()

    def test_yaml_module( self ):
        type_registry = builtin_type_registry()
        fpath = os.path.join(os.path.dirname(__file__), 'test_module1.types.yaml')
        registry = resolve_typedefs_from_yaml_file(self.meta_type_registry, type_registry, fpath)

        self.assertTrue(registry.has_name('some_int'))
        self.assertEqual(tInt, registry.get_name('some_int'))

        self.assertTrue(registry.has_name('simple_class'))
        self.assertEqual(TClass(tObject, 'simple', TRecord([])), registry.get_name('simple_class'))

        self.assertTrue(registry.has_name('text_object'))
        self.assertEqual(TClass(tObject, 'text', TRecord(base=tBaseObject, fields=[Field('text', tString)])),
                         registry.get_name('text_object'))

    def test_types_module( self ):
        type_registry = builtin_type_registry()
        fpath = os.path.join(os.path.dirname(__file__), 'test_module1.types')
        typedefs, registry = load_types_file(self.meta_type_registry, type_registry, fpath)

        self.assertTrue(registry.has_name('some_int'))
        self.assertEqual(tInt, registry.get_name('some_int'))

        self.assertTrue(registry.has_name('simple_class'))
        self.assertEqual(TClass(tObject, 'simple_2', TRecord([])), registry.get_name('simple_class'))

        self.assertTrue(registry.has_name('text_object'))
        self.assertEqual(TClass(tObject, 'text_2', TRecord(base=tBaseObject, fields=[Field('text', tString)])),
                         registry.get_name('text_object'))
