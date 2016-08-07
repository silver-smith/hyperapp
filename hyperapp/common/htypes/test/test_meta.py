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
    OpenCommand,
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
    MetaNameRegistry,
    make_type_registry,
    builtin_type_names,
    )
from hyperapp.common.visual_rep import pprint

log = logging.getLogger(__name__)


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
        self.type_registry = make_type_registry()

    def test_named( self ):
        data = t_named('int')
        t = self.type_registry.resolve(MetaNameRegistry(), builtin_type_names(), data)
        self.assertEqual(t, tInt)
        self.assertIs(t, tInt)  # must resolve to same instance

    def test_optional( self ):
        data = t_optional_meta(t_named('string'))
        t = self.type_registry.resolve(MetaNameRegistry(), builtin_type_names(), data)
        self.assertEqual(t, TOptional(tString))
        self.assertIs(t.base_t, tString)

    def test_list( self ):
        data = t_list_meta(t_optional_meta(t_named('datetime')))
        t = self.type_registry.resolve(MetaNameRegistry(), builtin_type_names(), data)
        self.assertEqual(TList(TOptional(tDateTime)), t)

    ## def test_indexed_list( self ):
    ##     for element_t in self.primitive_types:
    ##         t = TIndexedList(element_t)
    ##         self.check_type(t)

    def test_record( self ):
        data = t_record_meta([
            t_field_meta('int_field', t_named('int')),
            t_field_meta('string_list_field', t_list_meta(t_named('string'))),
            t_field_meta('bool_optional_field', t_optional_meta(t_named('bool'))),
            ])
        t = self.type_registry.resolve(MetaNameRegistry(), builtin_type_names(), data)
        self.assertEqual(TRecord([
            Field('int_field', tInt),
            Field('string_list_field', TList(tString)),
            Field('bool_optional_field', TOptional(tBool)),
            ]),
            t)

    def test_hierarchy( self ):
        meta_names = MetaNameRegistry()
        builtins = builtin_type_names()
        hdata = t_hierarchy_meta('test_hierarchy')
        meta_names.register('my_test_hierarchy', hdata)
        hierarchy = self.type_registry.resolve(meta_names, builtins, hdata)

        cdata_a = t_hierarchy_class_meta('my_test_hierarchy', 'class_a', base_name=None, fields=[
            t_field_meta('field_a_1', t_named('string')),
            ])
        meta_names.register('my_class_a', cdata_a)
        cdata_b = t_hierarchy_class_meta('my_test_hierarchy', 'class_b', base_name='my_class_a', fields=[
            t_field_meta('field_b_1', t_list_meta(t_named('int'))),
            ])
        meta_names.register('my_class_b', cdata_b)
        self.assertEqual(THierarchy('test_hierarchy'), hierarchy)
        class_a = self.type_registry.resolve(meta_names, builtins, cdata_a)
        self.assertEqual(TClass(hierarchy, 'class_a', TRecord([Field('field_a_1', tString)])), class_a)

    def test_interface( self ):
        data = t_interface_meta('unit_test_iface', [
            t_command_meta('request', 'request_one',
                           [t_field_meta('req_param1', t_named('string'))],
                           [t_field_meta('req_result1', t_list_meta(t_named('int')))]),
            t_command_meta('notification', 'notification_one',
                           [t_field_meta('noti_param1', t_optional_meta(t_named('bool'))),
                            t_field_meta('noti_param2', t_named('datetime'))])
                           ])
        data.iface_id = data.iface_id + '_new'  # hack to prevent tObject etc registration dup
        t = self.type_registry.resolve(MetaNameRegistry(), builtin_type_names(), data)
        t.iface_id = 'unit_test_iface'  # hack it back for comparision
        self.assertEqual(Interface('unit_test_iface', commands=[
            RequestCmd('request_one',
                       [Field('req_param1', tString)],
                       [Field('req_result1', TList(tInt))]),
            NotificationCmd('notification_one',
                            [Field('noti_param1', TOptional(tBool)),
                             Field('noti_param2', tDateTime)]),
            ## OpenCommand('open_command'),
            ]), t)
