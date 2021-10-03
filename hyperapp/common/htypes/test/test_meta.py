# test types serialization

import logging
import pytest

from hyperapp.common.htypes import (
    TPrimitive,
    tNone,
    tString,
    tBinary,
    tInt,
    tBool,
    tDateTime,
    TOptional,
    TRecord,
    TException,
    TList,
    Request,
    Notification,
    Interface,
    builtin_mt,
    name_wrapped_mt,
    optional_mt,
    list_mt,
    field_mt,
    record_mt,
    exception_mt,
    request_mt,
    notification_mt,
    interface_mt,
    )
from hyperapp.common import cdr_coders  # register codec

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.htypes.test.fixtures']


def test_optional(types, mosaic):
    base_ref = mosaic.put(builtin_mt('string'))
    piece = optional_mt(base_ref)
    t = types.resolve(mosaic.put(piece))
    assert t == TOptional(tString)
    assert t.base_t is tString


def test_list(types, mosaic):
    element_ref = mosaic.put(builtin_mt('int'))
    piece = list_mt(element_ref)
    t = types.resolve(mosaic.put(piece))
    assert t == TList(tInt)


def test_list_opt(types, mosaic):
    base_ref = mosaic.put(builtin_mt('datetime'))
    element_ref = mosaic.put(optional_mt(base_ref))
    piece = list_mt(element_ref)
    t = types.resolve(mosaic.put(piece))
    assert t == TList(TOptional(tDateTime))


def test_record(types, mosaic):
    string_list_mt = list_mt(mosaic.put(builtin_mt('string')))
    bool_opt_mt = optional_mt(mosaic.put(builtin_mt('bool')))
    piece = record_mt(None, [
        field_mt('int_field', mosaic.put(builtin_mt('int'))),
        field_mt('string_list_field', mosaic.put(string_list_mt)),
        field_mt('bool_optional_field', mosaic.put(bool_opt_mt)),
        ])
    name = 'some_test_record'
    named_piece = name_wrapped_mt(name, mosaic.put(piece))
    t = types.resolve(mosaic.put(named_piece))
    assert t == TRecord(name, {
        'int_field': tInt,
        'string_list_field': TList(tString),
        'bool_optional_field': TOptional(tBool),
        })


def test_based_record(types, mosaic):
    base_piece = record_mt(None, [
        field_mt('int_field', mosaic.put(builtin_mt('int'))),
        ])
    named_base_piece = name_wrapped_mt('some_base_record', mosaic.put(base_piece))
    named_base_ref = mosaic.put(named_base_piece)
    piece = record_mt(named_base_ref, [
        field_mt('string_field', mosaic.put(builtin_mt('string'))),
        ])
    name = 'some_test_record'
    named_piece = name_wrapped_mt(name, mosaic.put(piece))
    t = types.resolve(mosaic.put(named_piece))
    assert t == TRecord(name, {
        'int_field': tInt,
        'string_field': tString,
        })


def test_empty_record(types, mosaic):
    piece = record_mt(None, [])

    name_1 = 'record_1'
    named_piece_1 = name_wrapped_mt(name_1, mosaic.put(piece))
    t_1 = types.resolve(mosaic.put(named_piece_1))
    assert t_1 == TRecord(name_1, {})

    name_2 = 'record_2'
    named_piece_2 = name_wrapped_mt(name_2, mosaic.put(piece))
    t_2 = types.resolve(mosaic.put(named_piece_2))
    assert t_2 == TRecord(name_2, {})


def test_exception(types, mosaic):
    string_list_mt = list_mt(mosaic.put(builtin_mt('string')))
    bool_opt_mt = optional_mt(mosaic.put(builtin_mt('bool')))
    piece = exception_mt(None, [
        field_mt('int_field', mosaic.put(builtin_mt('int'))),
        field_mt('string_list_field', mosaic.put(string_list_mt)),
        field_mt('bool_optional_field', mosaic.put(bool_opt_mt)),
        ])
    name = 'some_test_exception'
    named_piece = name_wrapped_mt(name, mosaic.put(piece))
    t = types.resolve(mosaic.put(named_piece))
    assert t == TException(name, {
        'int_field': tInt,
        'string_list_field': TList(tString),
        'bool_optional_field': TOptional(tBool),
        })


def test_based_exception(types, mosaic):
    base_piece = exception_mt(None, [
        field_mt('int_field', mosaic.put(builtin_mt('int'))),
        ])
    named_base_piece = name_wrapped_mt('some_base_exception', mosaic.put(base_piece))
    named_base_ref = mosaic.put(named_base_piece)
    piece = exception_mt(named_base_ref, [
        field_mt('string_field', mosaic.put(builtin_mt('string'))),
        ])
    name = 'some_test_exception'
    named_piece = name_wrapped_mt(name, mosaic.put(piece))
    t = types.resolve(mosaic.put(named_piece))
    assert t == TException(name, {
        'int_field': tInt,
        'string_field': tString,
        })


def test_empty_exception(types, mosaic):
    piece = exception_mt(None, [])

    name_1 = 'exception_1'
    named_piece_1 = name_wrapped_mt(name_1, mosaic.put(piece))
    t_1 = types.resolve(mosaic.put(named_piece_1))
    assert t_1 == TException(name_1, {})

    name_2 = 'exception_2'
    named_piece_2 = name_wrapped_mt(name_2, mosaic.put(piece))
    t_2 = types.resolve(mosaic.put(named_piece_2))
    assert t_2 == TException(name_2, {})


def test_interface(types, mosaic):
    int_list_mt = list_mt(mosaic.put(builtin_mt('int')))
    bool_opt_mt = optional_mt(mosaic.put(builtin_mt('bool')))
    request_1 = request_mt(
        method_name='request_1',
        param_fields=[
            field_mt('request_1_str_param', mosaic.put(builtin_mt('string'))),
            field_mt('request_1_int_list_param', mosaic.put(int_list_mt)),
            ],
        response_fields=[
            field_mt('request_1_int_response', mosaic.put(builtin_mt('int'))),
            field_mt('request_1_bool_opt_response', mosaic.put(bool_opt_mt)),
            ],
        )
    notification_1 = notification_mt(
        method_name='notification_1',
        param_fields=[
            field_mt('notification_1_datetime_param', mosaic.put(builtin_mt('datetime'))),
            field_mt('notification_1_bool_opt_param', mosaic.put(bool_opt_mt)),
            ],
        )
    request_2 = request_mt(
        method_name='request_2',
        param_fields=[
            field_mt('request_2_datetime_param', mosaic.put(builtin_mt('datetime'))),
        ],
        response_fields=[
            field_mt('request_2_str_response', mosaic.put(builtin_mt('string'))),
        ],
        )
    notification_2 = notification_mt(
        method_name='notification_2',
        param_fields=[
            field_mt('notification_2_int_list_param', mosaic.put(int_list_mt)),
        ],
        )
    request_3 = request_mt('request_3', param_fields=[], response_fields=[])
    notification_3 = notification_mt('notification_3', param_fields=[])

    piece = interface_mt(
        base=None,
        method_list=[
            mosaic.put(request_1),
            mosaic.put(notification_1),
            mosaic.put(request_2),
            mosaic.put(notification_2),
            mosaic.put(request_3),
            mosaic.put(notification_3),
            ],
        )

    name = 'test_interface'
    named_piece = name_wrapped_mt(name, mosaic.put(piece))
    t = types.resolve(mosaic.put(named_piece))

    assert t == Interface(name,
        method_list=[
            Request(
                method_name='request_1',
                params_record_t=TRecord(f'{name}_request_1_params', {
                    'request_1_str_param': tString,
                    'request_1_int_list_param': TList(tInt),
                }),
                response_record_t=TRecord(f'{name}_request_1_response', {
                    'request_1_int_response': tInt,
                    'request_1_bool_opt_response': TOptional(tBool),
                }),
            ),
            Notification(
                method_name='notification_1',
                params_record_t=TRecord(f'{name}_notification_1_params', {
                    'notification_1_datetime_param': tDateTime,
                    'notification_1_bool_opt_param': TOptional(tBool),
                    }),
                ),
            Request(
                method_name='request_2',
                params_record_t=TRecord(f'{name}_request_2_params', {
                    'request_2_datetime_param': tDateTime,
                    }),
                response_record_t=TRecord(f'{name}_request_2_response', {
                    'request_2_str_response': tString,
                    }),
                ),
            Notification(
                method_name='notification_2',
                params_record_t=TRecord(f'{name}_notification_2_params', {
                    'notification_2_int_list_param': TList(tInt),
                    }),
                ),
            Request(
                method_name='request_3',
                params_record_t=TRecord(f'{name}_request_3_params'),
                response_record_t=TRecord(f'{name}_request_3_response'),
                ),
            Notification(
                method_name='notification_3',
                params_record_t=TRecord(f'{name}_notification_3_params'),
                ),
        ])


def test_based_interface(types, mosaic):
    int_list_mt = list_mt(mosaic.put(builtin_mt('int')))
    bool_opt_mt = optional_mt(mosaic.put(builtin_mt('bool')))
    request_1 = request_mt(
        method_name='request_1',
        param_fields=[
            field_mt('request_1_datetime_param', mosaic.put(builtin_mt('datetime'))),
        ],
        response_fields=[
            field_mt('request_1_str_response', mosaic.put(builtin_mt('string'))),
        ],
        )
    notification_1 = notification_mt(
        method_name='notification_1',
        param_fields=[
            field_mt('notification_1_int_list_param', mosaic.put(int_list_mt)),
        ],
        )

    base_interface_mt = interface_mt(
        base=None,
        method_list=[
            mosaic.put(request_1),
            ],
        )
    base_name = 'test_base_interface'
    named_base_interface_mt = name_wrapped_mt(base_name, mosaic.put(base_interface_mt))

    piece = interface_mt(
        base=mosaic.put(named_base_interface_mt),
        method_list=[
            mosaic.put(notification_1),
            ],
        )

    name = 'test_interface'
    named_piece = name_wrapped_mt(name, mosaic.put(piece))
    t = types.resolve(mosaic.put(named_piece))

    base_interface_t = Interface(base_name,
        method_list=[
            Request(
                method_name='request_1',
                params_record_t=TRecord(f'{base_name}_request_1_params', {
                    'request_1_datetime_param': tDateTime,
                    }),
                response_record_t=TRecord(f'{base_name}_request_1_response', {
                    'request_1_str_response': tString,
                    }),
                ),
            ])

    assert t == Interface(
        name=name,
        base=base_interface_t,
        method_list=[
            Notification(
                method_name='notification_1',
                params_record_t=TRecord(f'{name}_notification_1_params', {
                    'notification_1_int_list_param': TList(tInt),
                    }),
                ),
        ])
