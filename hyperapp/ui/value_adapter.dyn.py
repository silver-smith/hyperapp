from .code.mark import mark


class ValueAdapter:

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx, accessor_creg, convertor_creg):
        accessor = accessor_creg.invite(piece.accessor, model, ctx)
        cvt = convertor_creg.invite(piece.convertor)
        return cls(accessor, cvt)

    def __init__(self, accessor, cvt):
        self._accessor = accessor
        self._cvt = cvt

    def get_value(self):
        value = self._accessor.get_value()
        return self._cvt.value_to_view(value)

    def value_changed(self, view_value):
        old_value = self._accessor.get_value()
        new_value = self._cvt.view_to_value(old_value, view_value)
        self._accessor.value_changed(new_value)
