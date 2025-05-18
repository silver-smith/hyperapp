from hyperapp.boot.htypes import TOptional

from . import htypes
from .services import (
    code_registry_ctr,
    mosaic,
    )
from .code.mark import mark


class NoOpConvertor:

    @classmethod
    @mark.actor.convertor_creg
    def from_piece(cls, piece):
        return cls()

    def value_to_view(self, value):
        return value

    def view_to_value(self, old_value, view_value):
        return view_value


class IntToStringConvertor:

    @classmethod
    @mark.actor.convertor_creg
    def from_piece(cls, piece):
        return cls()

    def value_to_view(self, value):
        return str(value)

    def view_to_value(self, old_value, view_value):
        return int(view_value)


class OptionalConvertor:

    @classmethod
    @mark.actor.convertor_creg
    def from_piece(cls, piece, convertor_creg):
        base_cvt = convertor_creg.invite(piece.base)
        return cls(base_cvt)

    def __init__(self, base_cvt):
        self._base_cvt = base_cvt

    def value_to_view(self, value):
        if value is None:
            return ''
        else:
            return self._base_cvt.value_to_view(value)

    def view_to_value(self, old_value, view_value):
        if not view_value:
            return None
        return self._base_cvt.view_to_value(old_value, view_value)


@mark.service
def convertor_creg(config):
    return code_registry_ctr('convertor_creg', config)


def type_to_text_convertor(t):
    if t is htypes.builtin.string:
        return htypes.type_convertor.noop_convertor()
    if t is htypes.builtin.int:
        return htypes.type_convertor.int_to_string_convertor()
    if isinstance(t, TOptional):
        return htypes.type_convertor.opt_convertor(
            base=mosaic.put(type_to_text_convertor(t.base_t)),
            )
    raise RuntimeError(f"Unsupported type for convertor: {t}")
