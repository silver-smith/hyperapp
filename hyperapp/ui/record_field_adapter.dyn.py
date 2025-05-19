from .services import (
    pyobj_creg,
    )
from .code.mark import mark


class RecordFieldAdapter:

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx, ui_adapter_creg, convertor_creg):
        base = ui_adapter_creg.invite(piece.record_adapter, model, ctx)
        field_t = pyobj_creg.invite(piece.field_t)
        cvt = convertor_creg.invite(piece.cvt)
        return cls(base, piece.field_name, field_t, cvt)

    def __init__(self, record_adapter, field_name, field_t, cvt):
        self._record_adapter = record_adapter
        self._field_name = field_name
        self._field_t = field_t
        self._cvt = cvt

    @property
    def value(self):
        return getattr(self._record_adapter.get_value(), self._field_name)

    def get_view_value(self):
        return self._cvt.value_to_view(self.value)

    def text_to_value(self, text):
        return self._cvt.view_to_value(self.value, text)

    def value_changed(self, text):
        new_value = self._cvt.view_to_value(self.value, text)
        self._record_adapter.field_changed(self._field_name, new_value)
