from hyperapp.boot.htypes import TOptional

from . import htypes
from .services import (
    mosaic,
    )
from .tested.code import type_convertor


def test_noop_convertor():
    piece = htypes.type_convertor.noop_convertor()
    cvt = type_convertor.NoOpConvertor.from_piece(piece)
    assert cvt.value_to_view(123) == 123
    assert cvt.view_to_value(0, 123) == 123


def test_int_to_string_convertor():
    piece = htypes.type_convertor.int_to_string_convertor()
    cvt = type_convertor.IntToStringConvertor.from_piece(piece)
    assert cvt.value_to_view(123) == '123'
    assert cvt.view_to_value(0, '123') == 123


def test_optional_convertor():
    base_piece = htypes.type_convertor.int_to_string_convertor()
    piece = htypes.type_convertor.opt_convertor(
        base=mosaic.put(base_piece),
        )
    cvt = type_convertor.OptionalConvertor.from_piece(piece)
    assert cvt.value_to_view(123) == '123'
    assert cvt.view_to_value(0, '123') == 123
    assert cvt.value_to_view(None) == ''
    assert cvt.view_to_value(0, '') == None


def test_string_to_text_cvt():
    cvt = type_convertor.type_to_text_convertor(htypes.builtin.string)
    assert cvt == htypes.type_convertor.noop_convertor()


def test_int_to_text_cvt():
    cvt = type_convertor.type_to_text_convertor(htypes.builtin.int)
    assert cvt == htypes.type_convertor.int_to_string_convertor()


def test_int_opt_to_text_cvt():
    cvt = type_convertor.type_to_text_convertor(TOptional(htypes.builtin.int))
    assert isinstance(cvt, htypes.type_convertor.opt_convertor)
