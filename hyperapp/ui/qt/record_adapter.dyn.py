import logging
import weakref

from .services import (
    feed_factory,
    pyobj_creg,
    )

log = logging.getLogger(__name__)


class FnRecordAdapter:

    @classmethod
    def from_piece(cls, piece, model, ctx):
        record_t = pyobj_creg.invite(piece.record_t)
        fn = pyobj_creg.invite(piece.function)
        return cls(model, record_t, piece.params, ctx, fn)

    def __init__(self, model, record_t, params, ctx, fn):
        self._model = model
        self._record_t = record_t
        self._params = params
        self._ctx = ctx
        self._fn = fn
        self._subscribers = weakref.WeakSet()
        self._record = None
        try:
            self._feed = feed_factory(model)
        except KeyError:
            self._feed = None
        else:
            self._feed.subscribe(self)

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    @property
    def model(self):
        return self._model

    def process_diff(self, diff):
        log.info("Record adapter: process diff: %s", diff)
        for subscriber in self._subscribers:
            subscriber.process_diff(diff)

    @property
    def record_t(self):
        return self._record_t

    def get_field(self, name):
        if self._record is None:
            self._populate()
        return getattr(self._record, name)

    def _populate(self):
        available_params = {
            **self._ctx.as_dict(),
            'piece': self._model,
            'feed': self._feed,
            'ctx': self._ctx,
            }
        kw = {
            name: available_params[name]
            for name in self._params
            }
        self._record = self._call_fn(**kw)

    def _call_fn(self, **kw):
        return self._fn(**kw)
