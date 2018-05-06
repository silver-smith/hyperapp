import os.path
import unittest
from pathlib import Path

from hyperapp.common.htypes import (
    tInt,
    tString,
    Field,
    TRecord,
    TList,
    TClass,
    tTypeDef,
    t_named,
    make_meta_type_registry,
    builtin_type_registry,
    builtin_type_registry_registry,
    TypeResolver,
    )
from hyperapp.common.type_module import (
    resolve_typedefs_from_yaml_file,
    load_types_file,
    resolve_typedefs,
    )
from hyperapp.common import dict_coders, cdr_coders


TEST_TYPE_MODULES_DIR = Path(__file__).parent.resolve()


class TypeModuleTest(unittest.TestCase):

    def setUp(self):
        self.meta_type_registry = make_meta_type_registry()

    def make_fpath(self, module_name):
        return TEST_TYPE_MODULES_DIR / module_name

    def test_types_module(self):
        type_registry_registry = builtin_type_registry_registry()
        used_modules1, typedefs1, registry1 = load_types_file(
            self.meta_type_registry, type_registry_registry, 'test_module1', self.make_fpath('test_module1.types'))

        self.assertTrue(registry1.has_name('some_int'))
        self.assertEqual(tInt, registry1.get_name('some_int'))

        self.assertTrue(registry1.has_name('object'))
        object_t = registry1.get_name('object')

        self.assertTrue(registry1.has_name('simple_class'))
        simple_class = registry1.get_name('simple_class')
        self.assertEqual(TClass(object_t, 'simple_2', TRecord([])), simple_class)

        self.assertTrue(registry1.has_name('text_object'))
        self.assertEqual(TClass(object_t, 'text_2', base=simple_class, trec=TRecord([Field('text', tString)])),
                         registry1.get_name('text_object'))

        self.assertEqual([], used_modules1)

        type_registry_registry.register('test_module1', registry1)

        used_modules2, typedefs2, registry2 = load_types_file(
            self.meta_type_registry, type_registry_registry, 'test_module2', self.make_fpath('test_module2.types'))

