from .services import (
    code_registry_ctr,
    mosaic,
    )
from .code.mark import mark


class ModelAccessor:

    @classmethod
    @mark.actor.accessor_creg
    def from_piece(cls, piece, model, ctx):
        return cls(model)

    def __init__(self, model):
        self._model = model

    def get_value(self):
        return self._model

    def value_changed(self, new_value):
        pass


class RecordFieldAccessor:

    @classmethod
    @mark.actor.accessor_creg
    def from_piece(cls, piece, model, ctx, ui_adapter_creg):
        record_adapter = ui_adapter_creg.invite(piece.record_adapter, model, ctx)
        return cls(record_adapter, piece.field_name)

    def __init__(self, record_adapter, field_name):
        self._record_adapter = record_adapter
        self._field_name = field_name

    def get_value(self):
        record = self._record_adapter.get_value()
        return getattr(record, self._field_name)

    def value_changed(self, new_value):
        self._record_adapter.field_changed(self._field_name, new_value)


@mark.service
def accessor_creg(config):
    return code_registry_ctr('accessor_creg', config)
