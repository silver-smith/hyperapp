from .code.mark import mark


class RecordFieldAdapter:

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx, ui_adapter_creg):
        base = ui_adapter_creg.invite(piece.record_adapter, model, ctx)
        return cls(base, piece.field_name)

    def __init__(self, record_adapter, field_name):
        self._record_adapter = record_adapter
        self._field_name = field_name

    @property
    def value(self):
        return getattr(self._record_adapter.value, self._field_name)

    def get_text(self):
        return str(self.value)

    def value_changed(self, new_value):
        self._record_adapter.field_changed(self._field_name, new_value)
