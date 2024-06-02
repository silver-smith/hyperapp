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
    builtin_mt,
    name_wrapped_mt,
    optional_mt,
    list_mt,
    field_mt,
    record_mt,
    exception_mt,
    )
from hyperapp.common import cdr_coders  # register codec

log = logging.getLogger(__name__)


def test_optional(pyobj_creg, mosaic):
    base_ref = mosaic.put(builtin_mt('string'))
    piece = optional_mt(base_ref)
    t = pyobj_creg.animate(piece)
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
    piece = record_mt(None, (
        field_mt('int_field', mosaic.put(builtin_mt('int'))),
        field_mt('string_list_field', mosaic.put(string_list_mt)),
        field_mt('bool_optional_field', mosaic.put(bool_opt_mt)),
        ))
    module_name = 'test'
    name = 'some_test_record'
    named_piece = name_wrapped_mt(module_name, name, mosaic.put(piece))
    t = types.resolve(mosaic.put(named_piece))
    assert t == TRecord(module_name, name, {
        'int_field': tInt,
        'string_list_field': TList(tString),
        'bool_optional_field': TOptional(tBool),
        })


def test_based_record(types, mosaic):
    base_piece = record_mt(None, (
        field_mt('int_field', mosaic.put(builtin_mt('int'))),
        ))
    named_base_piece = name_wrapped_mt('test', 'some_base_record', mosaic.put(base_piece))
    named_base_ref = mosaic.put(named_base_piece)
    piece = record_mt(named_base_ref, (
        field_mt('string_field', mosaic.put(builtin_mt('string'))),
        ))
    module_name = 'test'
    name = 'some_test_record'
    named_piece = name_wrapped_mt(module_name, name, mosaic.put(piece))
    t = types.resolve(mosaic.put(named_piece))
    assert t == TRecord(module_name, name, {
        'int_field': tInt,
        'string_field': tString,
        })


def test_empty_record(types, mosaic):
    piece = record_mt(None, ())

    name_1 = 'record_1'
    named_piece_1 = name_wrapped_mt('test', name_1, mosaic.put(piece))
    t_1 = types.resolve(mosaic.put(named_piece_1))
    assert t_1 == TRecord('test', name_1, {})

    name_2 = 'record_2'
    named_piece_2 = name_wrapped_mt('test', name_2, mosaic.put(piece))
    t_2 = types.resolve(mosaic.put(named_piece_2))
    assert t_2 == TRecord('test', name_2, {})


def test_exception(types, mosaic):
    string_list_mt = list_mt(mosaic.put(builtin_mt('string')))
    bool_opt_mt = optional_mt(mosaic.put(builtin_mt('bool')))
    piece = exception_mt(None, (
        field_mt('int_field', mosaic.put(builtin_mt('int'))),
        field_mt('string_list_field', mosaic.put(string_list_mt)),
        field_mt('bool_optional_field', mosaic.put(bool_opt_mt)),
        ))
    module_name = 'test'
    name = 'some_test_exception'
    named_piece = name_wrapped_mt(module_name, name, mosaic.put(piece))
    t = types.resolve(mosaic.put(named_piece))
    assert t == TException(module_name, name, {
        'int_field': tInt,
        'string_list_field': TList(tString),
        'bool_optional_field': TOptional(tBool),
        })


def test_based_exception(types, mosaic):
    base_piece = exception_mt(None, (
        field_mt('int_field', mosaic.put(builtin_mt('int'))),
        ))
    named_base_piece = name_wrapped_mt('test', 'some_base_exception', mosaic.put(base_piece))
    named_base_ref = mosaic.put(named_base_piece)
    piece = exception_mt(named_base_ref, (
        field_mt('string_field', mosaic.put(builtin_mt('string'))),
        ))
    module_name = 'test'
    name = 'some_test_exception'
    named_piece = name_wrapped_mt(module_name, name, mosaic.put(piece))
    t = types.resolve(mosaic.put(named_piece))
    assert t == TException(module_name, name, {
        'int_field': tInt,
        'string_field': tString,
        })


def test_empty_exception(types, mosaic):
    piece = exception_mt(None, ())

    name_1 = 'exception_1'
    named_piece_1 = name_wrapped_mt('test', name_1, mosaic.put(piece))
    t_1 = types.resolve(mosaic.put(named_piece_1))
    assert t_1 == TException('test', name_1, {})

    name_2 = 'exception_2'
    named_piece_2 = name_wrapped_mt('test', name_2, mosaic.put(piece))
    t_2 = types.resolve(mosaic.put(named_piece_2))
    assert t_2 == TException('test', name_2, {})
