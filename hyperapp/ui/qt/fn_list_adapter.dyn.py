import logging
from functools import partial

from . import htypes
from .services import (
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.system_fn import ContextFn
from .code.list_adapter import IndexListAdapterMixin, KeyListAdapterMixin, FnListAdapterBase
from .code.list_servant_wrapper import list_wrapper

log = logging.getLogger(__name__)


class FnListAdapter(FnListAdapterBase):

    @staticmethod
    def _resolve_model(peer_registry, model):
        if isinstance(model, htypes.model.remote_model):
            remote_peer = peer_registry.invite(model.remote_peer)
            real_model = web.summon(model.model)
        else:
            remote_peer = None
            real_model = model
        return (remote_peer, real_model)

    def __init__(self, system_fn_creg, rpc_system_call_factory, client_feed_factory, model_servant, column_visible_reg,
                 model, real_model, item_t, remote_peer, ctx, fn):
        assert not (remote_peer and 'ctx' in fn.ctx_params)  # Functions with 'ctx' param are not remotable.
        super().__init__(column_visible_reg, real_model, item_t)
        self._system_fn_creg = system_fn_creg
        self._rpc_system_call_factory = rpc_system_call_factory
        self._model_servant = model_servant
        self._remote_peer = remote_peer
        self._ctx = ctx
        self._fn = fn
        try:
            self._feed = client_feed_factory(model, ctx)
        except KeyError:
            self._feed = None
        else:
            self._feed.subscribe(self)

    @property
    def function(self):
        return self._fn

    def _call_fn(self, **kw):
        if self._remote_peer:
            remote_peer = self._remote_peer
        else:
            try:
                remote_peer = self._ctx.remote_peer
            except KeyError:
                remote_peer = None
        wrapper_fn = self._wrapper_fn()
        wrapper_kw = {
            **kw,
            'servant_fn_piece': self._fn.piece,
            'key_field': self.key_field,
            'key_field_t': pyobj_creg.actor_to_piece_opt(self.key_field_t),
            }
        if remote_peer:
            rpc_call = self._rpc_system_call_factory(
                receiver_peer=remote_peer,
                sender_identity=self._ctx.identity,
                fn=wrapper_fn,
                )
            call_kw = wrapper_fn.call_kw(self._ctx, **wrapper_kw)
            return rpc_call(**call_kw)
        else:
            return wrapper_fn.call(self._ctx, **wrapper_kw)

    def _wrapper_fn(self):
        return ContextFn(
            rpc_system_call_factory=self._rpc_system_call_factory,
            ctx_params=('servant_fn_piece', 'model', 'key_field', 'key_field_t', *self._fn.ctx_params),
            service_params=('system_fn_creg', 'model_servant'),
            raw_fn=list_wrapper,
            bound_fn=partial(
                list_wrapper,
                system_fn_creg=self._system_fn_creg,
                model_servant=self._model_servant,
                ),
            )


class FnIndexListAdapter(FnListAdapter, IndexListAdapterMixin):

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx,
                   system_fn_creg, rpc_system_call_factory, client_feed_factory, model_servant, column_visible_reg, peer_registry):
        item_t = pyobj_creg.invite(piece.item_t)
        fn = system_fn_creg.invite(piece.system_fn)
        remote_peer, real_model = cls._resolve_model(peer_registry, model)
        return cls(system_fn_creg, rpc_system_call_factory, client_feed_factory, model_servant, column_visible_reg,
                   model, real_model, item_t, remote_peer, ctx, fn)
    

class FnKeyListAdapter(FnListAdapter, KeyListAdapterMixin):

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx,
                   system_fn_creg, rpc_system_call_factory, client_feed_factory, model_servant, column_visible_reg, peer_registry):
        item_t = pyobj_creg.invite(piece.item_t)
        fn = system_fn_creg.invite(piece.system_fn)
        remote_peer, real_model = cls._resolve_model(peer_registry, model)
        key_field_t = pyobj_creg.invite(piece.key_field_t)
        return cls(system_fn_creg, rpc_system_call_factory, client_feed_factory, model_servant, column_visible_reg,
                   model, real_model, item_t, remote_peer, ctx, fn, piece.key_field, key_field_t)

    def __init__(self, system_fn_creg, rpc_system_call_factory, client_feed_factory, model_servant, column_visible_reg,
                 model, real_model, item_t, remote_peer, ctx, fn, key_field, key_field_t):
        super().__init__(system_fn_creg, rpc_system_call_factory, client_feed_factory, model_servant, column_visible_reg,
                         model, real_model, item_t, remote_peer, ctx, fn)
        KeyListAdapterMixin.__init__(self, key_field, key_field_t)
