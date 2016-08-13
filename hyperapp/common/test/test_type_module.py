import os.path
import unittest
from hyperapp.common.htypes import (
    tInt,
    tString,
    Field,
    TRecord,
    TClass,
    tObject,
    tBaseObject,
    t_named,
    make_meta_type_registry,
    builtin_type_registry,
    )
from hyperapp.common.type_module import resolve_typedefs_from_yaml_file, resolve_typedefs_from_types_file


class TypeModuleTest(unittest.TestCase):

    def setUp( self ):
        self.meta_type_registry = make_meta_type_registry()

    def test_yaml_module( self ):
        type_registry = builtin_type_registry()
        fname = os.path.join(os.path.dirname(__file__), 'test_module1.types.yaml')
        module = resolve_typedefs_from_yaml_file(self.meta_type_registry, type_registry, fname)

        self.assertTrue(hasattr(module, 'some_int'))
        self.assertEqual(tInt, module.some_int)

        self.assertTrue(hasattr(module, 'simple_class'))
        self.assertEqual(TClass(tObject, 'simple', TRecord([])), module.simple_class)

        self.assertTrue(hasattr(module, 'text_object'))
        self.assertEqual(TClass(tObject, 'text', TRecord(base=tBaseObject, fields=[Field('text', tString)])),
                         module.text_object)

    def test_types_module( self ):
        type_registry = builtin_type_registry()
        fname = os.path.join(os.path.dirname(__file__), 'test_module1.types')
        module = resolve_typedefs_from_types_file(self.meta_type_registry, type_registry, fname)

        self.assertTrue(hasattr(module, 'some_int'))
        self.assertEqual(tInt, module.some_int)

        self.assertTrue(hasattr(module, 'simple_class'))
        self.assertEqual(TClass(tObject, 'simple_2', TRecord([])), module.simple_class)

        self.assertTrue(hasattr(module, 'text_object'))
        self.assertEqual(TClass(tObject, 'text_2', TRecord(base=tBaseObject, fields=[Field('text', tString)])),
                         module.text_object)
