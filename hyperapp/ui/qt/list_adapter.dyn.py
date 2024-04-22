import abc
import logging
import weakref

from hyperapp.common.htypes import TList
from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from .services import (
    feed_factory,
    mosaic,
    peer_registry,
    pyobj_creg,
    rpc_call_factory,
    types,
    web,
    )
from .code.list_diff import ListDiff

log = logging.getLogger(__name__)


class StaticListAdapter:

    @classmethod
    def from_piece(cls, piece, ctx):
        value = web.summon(piece.value)
        list_t = deduce_complex_value_type(mosaic, types, value)
        assert isinstance(list_t, TList), repr(list_t)
        return cls(list_t.element_t, value)

    def __init__(self, item_t, value):
        self._item_t = item_t
        self._value = value  # record list.
        self._column_names = sorted(self._item_t.fields)

    @property
    def feed(self):
        return None

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

    def subscribe(self, model):
        pass


class FnListAdapterBase(metaclass=abc.ABCMeta):

    def __init__(self, model_piece, item_t, want_feed):
        self._model_piece = model_piece
        self._item_t = item_t
        self._want_feed = want_feed
        self._column_names = sorted(self._item_t.fields)
        self._item_list = None
        self._subscribers = weakref.WeakSet()
        if want_feed:
            self.feed = feed_factory(model_piece)
            self.feed.subscribe(self)
        else:
            self.feed = None

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    @property
    def model(self):
        return self._model_piece

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
        if not isinstance(diff, ListDiff.Append):
            raise NotImplementedError(diff)
        self._item_list.append(diff.item)
        for subscriber in self._subscribers:
            subscriber.process_diff(diff)

    @property
    def _items(self):
        if self._item_list is not None:
            return self._item_list
        self._populate()
        return self._item_list

    @abc.abstractmethod
    def _populate(self):
        pass


class FnListAdapter(FnListAdapterBase):

    @classmethod
    def from_piece(cls, piece, ctx):
        model_piece = web.summon(piece.model_piece)
        element_t = pyobj_creg.invite(piece.element_t)
        fn = pyobj_creg.invite(piece.function)
        return cls(model_piece, element_t, piece.want_feed, fn)

    def __init__(self, model_piece, item_t, want_feed, fn):
        super().__init__(model_piece, item_t, want_feed)
        self._fn = fn

    def _populate(self):
        kw = {'piece': self._model_piece}
        if self._want_feed:
            kw['feed'] = self.feed
        self._item_list = self._fn(**kw)


class RemoteFnListAdapter(FnListAdapterBase):

    @classmethod
    def from_piece(cls, piece, ctx):
        model_piece = web.summon(piece.model_piece)
        element_t = pyobj_creg.invite(piece.element_t)
        remote_peer = peer_registry.invite(piece.remote_peer)
        return cls(model_piece, element_t, piece.want_feed, piece.function, ctx.rpc_endpoint, ctx.identity, remote_peer)

    def __init__(self, model_piece, item_t, want_feed, fn_res_ref, rpc_endpoint, identity, remote_peer):
        super().__init__(model_piece, item_t, want_feed)
        self._rpc_call = rpc_call_factory(
            rpc_endpoint=rpc_endpoint,
            receiver_peer=remote_peer,
            servant_ref=fn_res_ref,
            sender_identity=identity,
            )

    def _populate(self):
        kw = {'piece': self._model_piece}
        if self._want_feed:
            kw['feed'] = self.feed
        self._item_list = self._rpc_call(**kw)
