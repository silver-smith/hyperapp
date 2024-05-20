import abc
import logging
import weakref

from hyperapp.common.htypes import TList

from .services import (
    deduce_t,
    feed_factory,
    peer_registry,
    pyobj_creg,
    rpc_call_factory,
    web,
    )
from .code.list_diff import ListDiff

log = logging.getLogger(__name__)


class StaticListAdapter:

    @classmethod
    def from_piece(cls, piece, model, ctx):
        list_t = deduce_t(model)
        assert isinstance(list_t, TList), repr(list_t)
        return cls(list_t.element_t, model)

    def __init__(self, item_t, value):
        self._item_t = item_t
        self._value = value  # record list.
        self._column_names = sorted(self._item_t.fields)

    def subscribe(self, model):
        pass

    @property
    def model(self):
        return self._value

    def column_count(self):
        return len(self._item_t.fields)

    def column_title(self, column):
        return self._column_names[column]

    def row_count(self):
        return len(self._value)

    def cell_data(self, row, column):
        return getattr(self._value[row], self._column_names[column])

    def get_item(self, idx):
        return self._value[idx]


class FnListAdapterBase(metaclass=abc.ABCMeta):

    def __init__(self, model, item_t, params, ctx):
        self._model = model
        self._item_t = item_t
        self._params = params
        self._ctx = ctx
        self._column_names = sorted(self._item_t.fields)
        self._item_list = None
        self._subscribers = weakref.WeakSet()
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

    def column_count(self):
        return len(self._item_t.fields)

    def column_title(self, column):
        return self._column_names[column]

    def row_count(self):
        return len(self._items)

    def cell_data(self, row, column):
        item = self._items[row]
        return getattr(item, self._column_names[column])

    def get_item(self, idx):
        return self._items[idx]

    def process_diff(self, diff):
        log.info("List adapter: process diff: %s", diff)
        if self._item_list is None:
            self._populate()
        if isinstance(diff, ListDiff.Append):
            self._item_list.append(diff.item)
        elif isinstance(diff, ListDiff.Replace):
            self._item_list[diff.idx] = diff.item
        else:
            raise NotImplementedError(diff)
        for subscriber in self._subscribers:
            subscriber.process_diff(diff)

    @property
    def element_t(self):
        return self._item_t

    @property
    def function_params(self):
        return self._params

    @property
    def _items(self):
        if self._item_list is not None:
            return self._item_list
        self._populate()
        return self._item_list

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
        self._item_list = self._call_fn(**kw)

    @abc.abstractmethod
    def _call_fn(self, **kw):
        pass


class FnListAdapter(FnListAdapterBase):

    @classmethod
    def from_piece(cls, piece, model, ctx):
        element_t = pyobj_creg.invite(piece.element_t)
        fn = pyobj_creg.invite(piece.function)
        return cls(model, element_t, piece.params, ctx, piece.function, fn)

    def __init__(self, model, item_t, params, ctx, fn_res_ref, fn):
        super().__init__(model, item_t, params, ctx)
        self._fn_res_ref = fn_res_ref
        self._fn = fn

    @property
    def function(self):
        return self._fn

    def _call_fn(self, **kw):
        try:
            rpc_endpoint = self._ctx.rpc_endpoint
            identity = self._ctx.identity
            remote_peer = self._ctx.remote_peer
        except KeyError:
            pass
        else:
            rpc_call = rpc_call_factory(
                rpc_endpoint=rpc_endpoint,
                sender_identity=identity,
                receiver_peer=remote_peer,
                servant_ref=self._fn_res_ref,
                )
            return rpc_call(**kw)
        return self._fn(**kw)


class RemoteFnListAdapter(FnListAdapterBase):

    @classmethod
    def from_piece(cls, piece, model, ctx):
        element_t = pyobj_creg.invite(piece.element_t)
        remote_peer = peer_registry.invite(piece.remote_peer)
        return cls(model, element_t, piece.params, ctx, piece.function, ctx.rpc_endpoint, ctx.identity, remote_peer)

    def __init__(self, model, item_t, params, ctx, fn_res_ref, rpc_endpoint, identity, remote_peer):
        super().__init__(model, item_t, params, ctx)
        self._rpc_call = rpc_call_factory(
            rpc_endpoint=rpc_endpoint,
            receiver_peer=remote_peer,
            servant_ref=fn_res_ref,
            sender_identity=identity,
            )

    def _call_fn(self, **kw):
        return self._rpc_call(**kw)
