# test types serialization

import logging
import unittest
from hyperapp.common.htypes import (
    TPrimitive,
    tNone,
    tString,
    tBinary,
    tInt,
    tBool,
    tDateTime,
    TOptional,
    Field,
    TRecord,
    TList,
    TIndexedList,
    tMetaType,
    TypeRegistry,
    )
from hyperapp.common.visual_rep import pprint


logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s  %(message)s')


class TypeSerializationTest(unittest.TestCase):

    primitive_types = [
        tNone,
        tString,
        tBinary,
        tInt,
        tBool,
        tDateTime,
        ]

    def setUp( self ):
        self.type_registry = TypeRegistry()
        for t in self.primitive_types:
            t.register(self.type_registry)
        TOptional.register(self.type_registry)
        TRecord.register(self.type_registry)
        TList.register(self.type_registry)
        TIndexedList.register(self.type_registry)

    def check_type( self, t ):
        print('Saving type:', t)
        data = t.to_data()
        pprint(tMetaType, data)
        self.assertIsInstance(data, tMetaType)
        resolved_t = self.type_registry.resolve(data)
        print('Loaded type:', resolved_t)
        self.assertEqual(resolved_t, t)

    def test_primitive( self ):
        for t in self.primitive_types:
            self.check_type(t)

    def test_optional( self ):
        for base_t in self.primitive_types:
            t = TOptional(base_t)
            self.check_type(t)

    def test_list( self ):
        for element_t in self.primitive_types:
            t = TList(element_t)
            self.check_type(t)

    def test_indexed_list( self ):
        for element_t in self.primitive_types:
            t = TIndexedList(element_t)
            self.check_type(t)

    def test_record( self ):
        t = TRecord([
            Field('string_field', tString),
            Field('int_field', tInt),
            Field('opt_binary_field', TOptional(tBinary)),
            ])
        self.check_type(t)
