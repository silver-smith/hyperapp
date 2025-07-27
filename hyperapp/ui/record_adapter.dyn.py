import logging
import weakref

from . import htypes
from .services import (
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.value_diff import SetValueDiff

log = logging.getLogger(__name__)


class RecordAdapter:

    def __init__(self, record_t):
        self._record_t = record_t

    @property
    def record_t(self):
        return self._record_t

    def get_field(self, name):
        return getattr(self.get_value(), name)


class StaticRecordAdapter(RecordAdapter):

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx):
        record_t = pyobj_creg.invite(piece.record_t)
        return cls(model, record_t)

    def __init__(self, model, record_t):
        super().__init__(record_t)
        self._model = model

    def subscribe(self, subscriber):
        pass

    def get_value(self):
        return self._model


class SharedValue:

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
        self._notify()

    def _notify(self):
        for subscriber in self._subscribers:
            subscriber.value_changed(self.value)

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    def process_diff(self, diff):
        log.info("Record adapter value: process diff: %s", diff)
        if isinstance(diff, SetValueDiff):
            self.value = diff.new_value
        else:
            raise NotImplementedError(f"Record adapter: {diff} is not implemented")
        self._notify()


class FnRecordAdapterBase(RecordAdapter):

    _model_to_value = weakref.WeakValueDictionary()

    @classmethod
    def _get_shared_value(cls, model, record_t):
        return cls._model_to_value.setdefault(model, SharedValue(record_t))

    def __init__(self, client_feed_factory, model, record_t, ctx, value):
        super().__init__(record_t)
        self._ctx = ctx
        self._value = value
        try:
            self._feed = client_feed_factory(model, ctx)
        except KeyError:
            self._feed = None
        else:
            self._feed.subscribe(self._value)

    def subscribe(self, subscriber):
        self._value.subscribe(subscriber)

    def get_value(self):
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
    def from_piece(cls, piece, model, ctx, system_fn_creg, peer_creg, rpc_system_call_factory, client_feed_factory):
        record_t = pyobj_creg.invite(piece.record_t)
        fn = system_fn_creg.invite(piece.system_fn)
        value = cls._get_shared_value(model, record_t)
        remote_peer, real_model = cls._resolve_model(peer_creg, model)
        return cls(rpc_system_call_factory, client_feed_factory, model, real_model, record_t, remote_peer, ctx, value, fn)

    @staticmethod
    def _resolve_model(peer_creg, model):
        if isinstance(model, htypes.model.remote_model):
            remote_peer = peer_creg.invite(model.remote_peer)
            real_model = web.summon(model.model)
        else:
            remote_peer = None
            real_model = model
        return (remote_peer, real_model)

    def __init__(self, rpc_system_call_factory, client_feed_factory, model, real_model, record_t, remote_peer, ctx, value, ctx_fn):
        super().__init__(client_feed_factory, model, record_t, ctx, value)
        self._rpc_system_call_factory = rpc_system_call_factory
        self._real_model = real_model
        self._remote_peer = remote_peer
        self._ctx_fn = ctx_fn

    def _get_value(self):
        additional_kw = {
            'model': self._real_model,
            'piece': self._real_model,
            }
        return self._call_fn(**additional_kw)

    def _call_fn(self, **kw):
        if self._remote_peer:
            rpc_call = self._rpc_system_call_factory(
                receiver_peer=self._remote_peer,
                sender_identity=self._ctx.identity,
                fn=self._ctx_fn,
                )
            call_kw = self._ctx_fn.call_kw(self._ctx, **kw)
            return rpc_call(**call_kw)
        else:
            return self._ctx_fn.call(self._ctx, **kw)
