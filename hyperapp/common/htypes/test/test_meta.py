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
    builtin_type_registry,
    TypeResolver,
    )

log = logging.getLogger(__name__)


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

    def test_named(self):
        resolver = TypeResolver([builtin_type_registry()])
        data = t_named('int')
        t = self.meta_type_registry.resolve(resolver, data)
        self.assertEqual(t, tInt)
        self.assertIs(t, tInt)  # must resolve to same instance

    def test_optional(self):
        resolver = TypeResolver([builtin_type_registry()])
        data = t_optional_meta(t_named('string'))
        t = self.meta_type_registry.resolve(resolver, data)
        self.assertEqual(t, TOptional(tString))
        self.assertIs(t.base_t, tString)

    def test_list(self):
        resolver = TypeResolver([builtin_type_registry()])
        data = t_list_meta(t_optional_meta(t_named('datetime')))
        t = self.meta_type_registry.resolve(resolver, data)
        self.assertEqual(TList(TOptional(tDateTime)), t)

    ## def test_indexed_list(self):
    ##     for element_t in self.primitive_types:
    ##         t = TIndexedList(element_t)
    ##         self.check_type(t)

    def test_record(self):
        resolver = TypeResolver([builtin_type_registry()])
        data = t_record_meta([
            t_field_meta('int_field', t_named('int')),
            t_field_meta('string_list_field', t_list_meta(t_named('string'))),
            t_field_meta('bool_optional_field', t_optional_meta(t_named('bool'))),
            ])
        t = self.meta_type_registry.resolve(resolver, data)
        self.assertEqual(TRecord([
            Field('int_field', tInt),
            Field('string_list_field', TList(tString)),
            Field('bool_optional_field', TOptional(tBool)),
            ]),
            t)

    def test_hierarchy(self):
        type_names = builtin_type_registry()
        resolver = TypeResolver([type_names])
        hdata = t_hierarchy_meta('test_hierarchy')
        hierarchy = self.meta_type_registry.resolve(resolver, hdata)
        type_names.register('my_test_hierarchy', hierarchy)

        cdata_a = t_hierarchy_class_meta('my_test_hierarchy', 'class_a', base_name=None, fields=[
            t_field_meta('field_a_1', t_named('string')),
            ])
        cdata_b = t_hierarchy_class_meta('my_test_hierarchy', 'class_b', base_name='my_class_a', fields=[
            t_field_meta('field_b_1', t_list_meta(t_named('int'))),
            ])
        self.assertTrue(THierarchy('test_hierarchy').matches(hierarchy))
        class_a = self.meta_type_registry.resolve(resolver, cdata_a)
        type_names.register('my_class_a', class_a)
        class_b = self.meta_type_registry.resolve(resolver, cdata_b)
        self.assertEqual(TClass(hierarchy, 'class_a', TRecord([Field('field_a_1', tString)])), class_a)
        self.assertEqual(TClass(hierarchy, 'class_b', TRecord([Field('field_a_1', tString),
                                                               Field('field_b_1', TList(tInt))])), class_b)

    def test_interface(self):
        type_names = builtin_type_registry()
        resolver = TypeResolver([type_names])
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
        t = self.meta_type_registry.resolve(resolver, data, full_name=['test_meta', 'test_iface'])
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
