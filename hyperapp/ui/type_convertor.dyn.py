from .services import (
    code_registry_ctr,
    )
from .code.mark import mark


class NoOpConvertor:

    @classmethod
    @mark.actor.convertor_creg
    def from_piece(cls, piece):
        return cls()

    def value_to_view(self, value):
        return value

    def view_to_value(self, value, view_value):
        return view_value


class IntToStringConvertor:

    @classmethod
    @mark.actor.convertor_creg
    def from_piece(cls, piece):
        return cls()

    def value_to_view(self, value):
        return str(value)

    def view_to_value(self, value, view_value):
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

    def view_to_value(self, value, view_value):
        if not view_value:
            return None
        return self._base_cvt.view_to_value(value, view_value)


@mark.service
def convertor_creg(config):
    return code_registry_ctr('convertor_creg', config)

