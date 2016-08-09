import os.path
import unittest
from hyperapp.common.htypes import (
    tInt,
    Field,
    TRecord,
    TClass,
    tObject,
    t_named,
    make_meta_type_registry,
    builtin_type_registry,
    )
from hyperapp.common.type_module import load_types_from_yaml_file


class TypeModuleTest(unittest.TestCase):

    def setUp( self ):
        self.meta_type_registry = make_meta_type_registry()

    def test_module1( self ):
        type_registry = builtin_type_registry()
        fname = os.path.join(os.path.dirname(__file__), 'test_module1.types.yaml')
        loaded_types = load_types_from_yaml_file(self.meta_type_registry, type_registry, fname)

        self.assertTrue(loaded_types.has_name('some_int'))
        self.assertEqual(tInt, loaded_types.get_name('some_int'))

        self.assertTrue(loaded_types.has_name('text_object'))
        self.assertEqual(TClass(tObject, 'text', TRecord([])), loaded_types.get_name('text_object'))
