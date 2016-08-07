import os.path
import unittest
from hyperapp.common.htypes import (
    tInt,
    t_named,
    MetaNameRegistry,
    builtin_type_names,
    make_type_registry,
    )
from hyperapp.common.type_module import load_types_from_yaml_file


class TypeModuleTest(unittest.TestCase):

    def setUp( self ):
        self.type_registry = make_type_registry()

    def test_module1( self ):
        type_names = builtin_type_names()
        fname = os.path.join(os.path.dirname(__file__), 'test_module1.types.yaml')
        meta_names = MetaNameRegistry()
        load_types_from_yaml_file(fname, type_names, self.type_registry, meta_names)
        self.assertTrue(meta_names.has_name('text_object'))
        t = self.type_registry.resolve(meta_names, type_names, t_named('text_object'))
        self.assertEqual(t, tInt)
