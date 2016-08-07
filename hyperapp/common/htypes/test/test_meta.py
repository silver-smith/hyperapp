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

    def check_type( self, t ):
        data = self.to_data(t)
        resolved_t = self.type_registry.resolve(data)
        log.info('Loaded type: %r', resolved_t)
        log.info('resolved:')
        resolved_data = resolved_t.to_data()
        pprint(tMetaType, resolved_data)
        self.assertEqual(resolved_t, t)

    def to_data( self, t ):
        log.info('Saving type: %r', t)
        data = t.to_data()
        self.assertIsInstance(data, tMetaType)
        pprint(tMetaType, data)
        return data

    ## def test_primitive( self ):
    ##     for t in self.primitive_types:
    ##         self.check_type(t)

    def test_named( self ):
        data = t_named('int')
        t = self.type_registry.resolve(builtin_type_names(), data)
        self.assertEqual(t, tInt)
        self.assertIs(t, tInt)  # must resolve to same instance

    def test_optional( self ):
        data = t_optional_meta(t_named('string'))
        t = self.type_registry.resolve(builtin_type_names(), data)
        self.assertEqual(t, TOptional(tString))
        self.assertIs(t.base_t, tString)

    def test_list( self ):
        data = t_list_meta(t_optional_meta(t_named('datetime')))
        t = self.type_registry.resolve(builtin_type_names(), data)
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
        t = self.type_registry.resolve(builtin_type_names(), data)
        self.assertEqual(TRecord([
            Field('int_field', tInt),
            Field('string_list_field', TList(tString)),
            Field('bool_optional_field', TOptional(tBool)),
            ]),
            t)

    ## def test_hierarchy( self ):
    ##     t = THierarchy('test_hierarchy')
    ##     class_a = t.register('class_a', fields=[Field('field_a_1', tString)])
    ##     class_b = t.register('class_b', base=class_a, fields=[Field('field_b_1', TList(tInt))])
    ##     self.check_type(t)

    ## def test_interface( self ):
    ##     t = Interface('meta_test_iface', commands=[
    ##         RequestCmd('request_one',
    ##                    [Field('request_param_1', tString)],
    ##                    [Field('request_result_1', tInt),
    ##                     Field('request_result_2', tBinary)]),
    ##         NotificationCmd('notification_one',
    ##                    [Field('notification_param_1', tDateTime),
    ##                     Field('notification_param_1', TList(tBool))]),
    ##         ## OpenCommand('open_command'),
    ##         ])
    ##     data = self.to_data(t)
    ##     data.iface_id = data.iface_id + '_new'  # hack to prevent tObject etc registration dup
    ##     resolved_t = self.type_registry.resolve(data)
    ##     log.info('Loaded type: %r', resolved_t)
    ##     self.assertEqual(data.iface_id, resolved_t.iface_id)
    ##     resolved_t.iface_id = t.iface_id  # hack it back for comparision
    ##     self.assertEqual(resolved_t, t)
