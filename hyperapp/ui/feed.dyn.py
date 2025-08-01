import logging
import weakref
from collections import defaultdict

from . import htypes
from .services import (
    deduce_t,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.context import Context
from .code.config_key_ctl import TypeKeyCtl
from .code.config_ctl import DictConfigCtl
from .code.system_fn import ContextFn
from .code.feed_servant import SubscriberIsGoneError, subscribe_server_feed, unsubscribe_server_feed

log = logging.getLogger(__name__)


class Feed:

    def __init__(self, peer_creg, rpc_system_call_factory, model):
        self._peer_creg = peer_creg
        self._rpc_system_call_factory = rpc_system_call_factory
        self._model = model
        self._close_hooks = []
        self._subscribed_to_remote_as = None
        self._subscribers = weakref.WeakSet()

    def add_close_hook(self, hook):
        self._close_hooks.append(hook)

    def subscribe(self, subscriber):
        # Note: finalize should be called before adding to subscribers to work.
        weakref.finalize(subscriber, self._subscriber_gone)
        self._subscribers.add(subscriber)

    def send(self, diff):
        log.info("Feed %s: Send: %s", self._model, diff)
        for subscriber in [*self._subscribers]:
            try:
                subscriber.process_diff(diff)
            except SubscriberIsGoneError as x:
                log.info("Feed %s: Subscriber %s is gone: %s", self._model, subscriber, x)
                self._subscribers.remove(subscriber)

    def subscribe_to_remote_feed(self, identity):
        if not isinstance(self._model, htypes.model.remote_model):
            return
        if self._subscribed_to_remote_as:
            assert self._subscribed_to_remote_as == identity  # Already subscribed with another identity.
            return
        self._call_remote_feed(identity, subscribe_server_feed)
        self._subscribed_to_remote_as = identity
        self.add_close_hook(self._unsubscribe_from_remote_feed)

    def _unsubscribe_from_remote_feed(self, model):
        assert model is self._model
        if not self._subscribed_to_remote_as:
            return  # Not subscribed to remote.
        self._call_remote_feed(self._subscribed_to_remote_as, unsubscribe_server_feed)

    def _call_remote_feed(self, identity, remote_fn):
        remote_peer = self._peer_creg.invite(self._model.remote_peer)
        real_model = web.summon(self._model.model)
        fn = ContextFn(
            rpc_system_call_factory=self._rpc_system_call_factory,
            ctx_params=('request', 'real_model'),
            service_params=('feed_factory', 'server_feed'),
            raw_fn=remote_fn,
            )
        rpc_call = self._rpc_system_call_factory(
            receiver_peer=remote_peer,
            sender_identity=identity,
            fn=fn,
            )
        ctx = Context(real_model=real_model)
        call_kw = fn.call_kw(ctx)
        rpc_call(**call_kw)

    def _subscriber_gone(self):
        if self._subscribers:
            return
        log.info("Feed %s: All subscribers are gone", self._model)
        for hook in self._close_hooks:
            hook(self._model)


class ListFeed(Feed):
    pass


class IndexTreeFeed(Feed):
    pass


class ValueFeed(Feed):
    pass


@mark.actor.feed_type_creg(htypes.feed.list_feed_type)
def list_feed_from_piece(piece):
    return ListFeed


@mark.actor.feed_type_creg(htypes.feed.index_tree_feed_type)
def index_tree_feed_from_piece(piece):
    return IndexTreeFeed


@mark.actor.feed_type_creg
def value_feed_from_piece(piece):
    return ValueFeed


@mark.service
def feed_map():
    return {}


@mark.service(ctl=DictConfigCtl(key_ctl=TypeKeyCtl()))
def feed_factory(config, peer_creg, rpc_system_call_factory, feed_map, piece):
    try:
        return feed_map[piece]
    except KeyError:
        pass

    def remove_feed(piece):
        del feed_map[piece]

    if isinstance(piece, htypes.model.remote_model):
        real_model = web.summon(piece.model)
    else:
        real_model = piece

    model_t = deduce_t(real_model)
    Feed = config[model_t]
    feed = Feed(peer_creg, rpc_system_call_factory, piece)
    feed_map[piece] = feed
    feed.add_close_hook(remove_feed)
    return feed


@mark.service
def client_feed_factory(feed_factory, piece, ctx):
    feed = feed_factory(piece)
    feed.subscribe_to_remote_feed(ctx.identity)
    return feed
