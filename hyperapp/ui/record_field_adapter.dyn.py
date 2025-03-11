from .services import (
    pyobj_creg,
    )
from .code.mark import mark


class RecordFieldAdapter:

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx, ui_adapter_creg):
        base = ui_adapter_creg.invite(piece.record_adapter, model, ctx)
        field_t = pyobj_creg.invite(piece.field_t)
        return cls(base, piece.field_name, field_t)

    def __init__(self, record_adapter, field_name, field_t):
        self._record_adapter = record_adapter
        self._field_name = field_name
        self._field_t = field_t

    @property
    def value(self):
        return getattr(self._record_adapter.value, self._field_name)

    def get_text(self):
        return str(self.value)

    def text_to_value(self, text):
        return self._field_t(text)

    def value_changed(self, new_value):
        self._record_adapter.field_changed(self._field_name, new_value)
