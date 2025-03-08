import logging
import weakref

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.construct_default_form import construct_default_form

log = logging.getLogger(__name__)


class RecordAdapter:

    def __init__(self, model, record_t):
        self._model = model
        self._record_t = record_t
        self._subscribers = weakref.WeakSet()

    @property
    def model(self):
        return self._model

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    def process_diff(self, diff):
        log.info("Record adapter: process diff: %s", diff)
        for subscriber in self._subscribers:
            subscriber.process_diff(diff)

    @property
    def record_t(self):
        return self._record_t

    def get_field(self, name):
        return getattr(self.value, name)


class StaticRecordAdapter(RecordAdapter):

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx):
        record_t = pyobj_creg.invite(piece.record_t)
        return cls(model, record_t)

    def __init__(self, model, record_t):
        super().__init__(model, record_t)

    @property
    def value(self):
        return self._model


class EditValue:

    # TODO: Add async lock for populating when populate method will become async.
    def __init__(self, value_t):
        self._value_t = value_t
        self.value = None
        self._subscribers = weakref.WeakSet()

    def set_field(self, field_name, new_value):
        kw = {
            **self.value._asdict(),
            **{field_name: new_value},
            }
        self.value = self._value_t(**kw)


class FnRecordAdapterBase(RecordAdapter):

    _model_to_value = weakref.WeakValueDictionary()

    @classmethod
    def _get_edit_value(cls, model, record_t):
        return cls._model_to_value.setdefault(model, EditValue(record_t))

    def __init__(self, feed_factory, model, record_t, ctx, value):
        super().__init__(model, record_t)
        self._ctx = ctx
        self._value = value
        try:
            self._feed = feed_factory(model)
        except KeyError:
            self._feed = None
        else:
            self._feed.subscribe(self)

    @property
    def value(self):
        if self._value.value is None:
            self._populate()
        return self._value.value

    def field_changed(self, field_name, new_value):
        self._value.set_field(field_name, new_value)

    def _populate(self):
        self._value.value = self._get_value()


class FnRecordAdapter(FnRecordAdapterBase):

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx, system_fn_creg, feed_factory):
        record_t = pyobj_creg.invite(piece.record_t)
        fn = system_fn_creg.invite(piece.system_fn)
        value = cls._get_edit_value(model, record_t)
        return cls(feed_factory, model, record_t, ctx, value, fn)

    @classmethod
    def _get_edit_value(cls, model, record_t):
        return cls._model_to_value.setdefault(model, EditValue(record_t))

    def __init__(self, feed_factory, model, record_t, ctx, value, ctx_fn):
        super().__init__(feed_factory, model, record_t, ctx, value)
        self._ctx_fn = ctx_fn

    def _get_value(self):
        additional_kw = {
            'model': self._model,
            'piece': self._model,
            'feed': self._feed,
            }
        return self._call_fn(**additional_kw)

    def _call_fn(self, **kw):
        return self._ctx_fn.call(self._ctx, **kw)


@mark.actor.ui_type_creg
def record_ui_type_layout(piece, system_fn_ref):
    record_t = pyobj_creg.invite(piece.record_t)
    adapter = htypes.record_adapter.fn_record_adapter(
        record_t=piece.record_t,
        system_fn=system_fn_ref,
        )
    return construct_default_form(adapter, record_t)
