import logging
import weakref

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark

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
        return getattr(self._record, name)


class StaticRecordAdapter(RecordAdapter):

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx):
        record_t = pyobj_creg.invite(piece.record_t)
        return cls(model, record_t)

    def __init__(self, model, record_t):
        super().__init__(model, record_t)
        self._record = model


class FnRecordAdapter(RecordAdapter):

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx, system_fn_creg, feed_factory):
        record_t = pyobj_creg.invite(piece.record_t)
        fn = system_fn_creg.invite(piece.system_fn)
        return cls(feed_factory, model, record_t, ctx, fn)

    def __init__(self, feed_factory, model, record_t, ctx, ctx_fn):
        super().__init__(model, record_t)
        self._ctx = ctx
        self._ctx_fn = ctx_fn
        self._record = None
        try:
            self._feed = feed_factory(model)
        except KeyError:
            self._feed = None
        else:
            self._feed.subscribe(self)

    def get_field(self, name):
        if self._record is None:
            self._populate()
        return super().get_field(name)

    def _populate(self):
        additional_kw = {
            'model': self._model,
            'piece': self._model,
            'feed': self._feed,
            }
        self._record = self._call_fn(**additional_kw)

    def _call_fn(self, **kw):
        return self._ctx_fn.call(self._ctx, **kw)


@mark.actor.ui_type_creg
def record_ui_type_layout(piece, system_fn_ref):
    adapter = htypes.record_adapter.fn_record_adapter(
        record_t=piece.record_t,
        system_fn=system_fn_ref,
        )
    return htypes.form.view(mosaic.put(adapter))
