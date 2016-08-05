# test types serialization

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
    tMetaType,
    TypeRegistry,
    )


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

    def test_primitive( self ):
        for t in self.primitive_types:
            data = t.to_data()
            self.assertIsInstance(data, tMetaType)
            resolved_t = self.type_registry.resolve(data)
            self.assertEqual(resolved_t, t)

    def test_optional( self ):
        for base_t in self.primitive_types:
            t = TOptional(base_t)
            data = t.to_data()
            self.assertIsInstance(data, tMetaType)
            resolved_t = self.type_registry.resolve(data)
            self.assertEqual(resolved_t, t)
