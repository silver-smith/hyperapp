import weakref

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
        self._subscribers = weakref.WeakSet()
        self._accessor.subscribe(self)

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    def value_changed(self, new_value):
        view_value = self._cvt.value_to_view(new_value)
        for subscriber in self._subscribers:
            subscriber.value_changed(view_value)

    def get_value(self):
        return self._accessor.get_value()

    def get_view_value(self):
        value = self._accessor.get_value()
        return self._cvt.value_to_view(value)

    def value_changed_by_me(self, view_value):
        new_value = self.view_to_value(view_value)
        self._accessor.value_changed_by_me(new_value)

    def view_to_value(self, view_value):
        old_value = self._accessor.get_value()
        return self._cvt.view_to_value(old_value, view_value)
