# test types serialization

import logging
import pytest
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
    TClass,
    THierarchy,
    RequestCmd,
    NotificationCmd,
    Interface,
    tMetaType,
    t_named,
    t_optional_meta,
    t_list_meta,
    t_field_meta,
    t_record_meta,
    t_hierarchy_meta,
    t_hierarchy_class_meta,
    t_command_meta,
    t_interface_meta,
    make_meta_type_registry,
    make_root_type_namespace,
    TypeNamespace,
    t_ref,
    builtin_ref_t,
    )
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.builtin_types_registry import make_builtin_types_registry
from hyperapp.common.ref_registry import RefRegistry
from hyperapp.common.ref_resolver import RefResolver
from hyperapp.common.type_resolver import TypeResolver

log = logging.getLogger(__name__)


@pytest.fixture
def types():
    return make_root_type_namespace()


@pytest.fixture
def ref_registry(types):
    return RefRegistry(types)


@pytest.fixture
def type_resolver(types, ref_registry):
    builtin_types_registry = make_builtin_types_registry()
    ref_resolver = RefResolver(types)
    ref_resolver.add_source(ref_registry)
    return TypeResolver(types, builtin_types_registry, ref_resolver)


@pytest.fixture
def builtin_ref(ref_registry):

    def make(name):
        ref = ref_registry.register_object(builtin_ref_t(['basic', name]))
        return t_ref(ref)

    return make


def test_optional(type_resolver, builtin_ref):
    data = t_optional_meta(builtin_ref('string'))
    t = type_resolver.resolve_meta_type(data, 'some_optional')
    assert t == TOptional(tString)
    assert t.base_t is tString


class MetaTypeTest(unittest.TestCase):

    primitive_types = [
        tNone,
        tString,
        tBinary,
        tInt,
        tBool,
        tDateTime,
        ]

    def setUp(self):
        self.meta_type_registry = make_meta_type_registry()
        self.types = make_root_type_namespace()
        self.module = TypeNamespace()
        self.resolver = TypeNameResolver([self.types.builtins, self.module])

    def resolve(self, data, full_name=None):
        return self.meta_type_registry.resolve(self.resolver, data, full_name=full_name)

    def test_named(self):
        data = t_named('int')
        t = self.resolve(data)
        self.assertEqual(t, tInt)
        self.assertIs(t, tInt)  # must resolve to same instance


    def test_list(self):
        data = t_list_meta(t_optional_meta(t_named('datetime')))
        t = self.resolve(data)
        self.assertEqual(TList(TOptional(tDateTime)), t)

    ## def test_indexed_list(self):
    ##     for element_t in self.primitive_types:
    ##         t = TIndexedList(element_t)
    ##         self.check_type(t)

    def test_record(self):
        data = t_record_meta([
            t_field_meta('int_field', t_named('int')),
            t_field_meta('string_list_field', t_list_meta(t_named('string'))),
            t_field_meta('bool_optional_field', t_optional_meta(t_named('bool'))),
            ])
        t = self.resolve(data)
        self.assertEqual(TRecord([
            Field('int_field', tInt),
            Field('string_list_field', TList(tString)),
            Field('bool_optional_field', TOptional(tBool)),
            ]), t)

    def test_based_record(self):
        base_record_data = t_record_meta([
            t_field_meta('int_field', t_named('int')),
            ])
        record_data = t_record_meta([
            t_field_meta('string_field', t_named('string')),
            ], base=base_record_data)
        t = self.resolve(record_data)
        self.assertEqual(TRecord([
            Field('int_field', tInt),
            Field('string_field', tString),
            ]), t)

    def test_hierarchy(self):
        hdata = t_hierarchy_meta('test_hierarchy')
        hierarchy = self.resolve(hdata)
        self.module['my_test_hierarchy'] = hierarchy

        cdata_a = t_hierarchy_class_meta('my_test_hierarchy', 'class_a', base_name=None, fields=[
            t_field_meta('field_a_1', t_named('string')),
            ])
        cdata_b = t_hierarchy_class_meta('my_test_hierarchy', 'class_b', base_name='my_class_a', fields=[
            t_field_meta('field_b_1', t_list_meta(t_named('int'))),
            ])
        self.assertTrue(THierarchy('test_hierarchy').matches(hierarchy))
        class_a = self.resolve(cdata_a)
        self.module['my_class_a'] = class_a
        class_b = self.resolve(cdata_b)
        self.assertEqual(TClass(hierarchy, 'class_a', TRecord([Field('field_a_1', tString)])), class_a)
        self.assertEqual(TClass(hierarchy, 'class_b', TRecord([Field('field_a_1', tString),
                                                               Field('field_b_1', TList(tInt))])), class_b)

    def test_interface(self):
        data = t_interface_meta(None, [
            t_command_meta('request', 'request_one',
                           [t_field_meta('req_param1', t_named('string'))],
                           [t_field_meta('req_result1', t_list_meta(t_named('int')))]),
            t_command_meta('notification', 'notification_one',
                           [t_field_meta('noti_param1', t_optional_meta(t_named('bool'))),
                            t_field_meta('noti_param2', t_named('datetime'))]),
            t_command_meta('request', 'request_open', [],
                           [t_field_meta('result', t_optional_meta(t_named('int')))]),
            ])
        t = self.resolve(data, full_name=['test_meta', 'test_iface'])
        self.assertEqual(Interface(['test_meta', 'test_iface'],
            commands=[
                RequestCmd(['test_meta', 'test_iface', 'request_one'], 'request_one',
                           [Field('req_param1', tString)],
                           [Field('req_result1', TList(tInt))]),
                NotificationCmd(['test_meta', 'test_iface', 'notification_one'], 'notification_one',
                                [Field('noti_param1', TOptional(tBool)),
                                 Field('noti_param2', tDateTime)]),
                RequestCmd(['test_meta', 'test_iface', 'request_open'], 'request_open', [],
                           [Field('result', TOptional(tInt))]),
            ]), t)
