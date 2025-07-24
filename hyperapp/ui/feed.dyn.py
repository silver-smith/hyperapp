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
from .code.config_key_ctl import TypeKeyCtl
from .code.config_ctl import DictConfigCtl
from .code.system_fn import ContextFn
from .code.feed_servant import subscribe_server_feed

log = logging.getLogger(__name__)


class Feed:

    def __init__(self, piece):
        self._piece = piece
        self._close_hooks = []
        self._subscribers = weakref.WeakSet()

    def add_close_hook(self, hook):
        self._close_hooks.append(hook)

    def subscribe(self, subscriber):
        # Note: finalize should be called first.
        weakref.finalize(subscriber, self._subscriber_gone)
        self._subscribers.add(subscriber)

    def send(self, diff):
        log.info("Feed: send: %s", diff)
        for subscriber in self._subscribers:
            subscriber.process_diff(diff)

    def _subscriber_gone(self):
        if self._subscribers:
            return
        for hook in self._close_hooks:
            hook(self._piece)


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
def feed_factory(config, feed_map, piece):
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
    feed = Feed(piece)
    feed_map[piece] = feed
    feed.add_close_hook(remove_feed)
    return feed


@mark.service
def remote_feed_receiver(diff_creg, feed_factory, piece, diff):
    diff_obj = diff_creg.animate(diff)
    log.info("Received remote diff: %s", diff_obj)
    feed = feed_factory(piece)
    feed.send(diff_obj)


def _subscribe_remote_feed(peer_registry, rpc_system_call_factory, remote_model, ctx):
    real_model = web.summon(remote_model.model)
    remote_peer = peer_registry.invite(remote_model.remote_peer)
    fn = ContextFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=('request', 'real_model'),
        service_params=('feed_factory', 'server_feed'),
        raw_fn=subscribe_server_feed,
        )
    rpc_call = rpc_system_call_factory(
        receiver_peer=remote_peer,
        sender_identity=ctx.identity,
        fn=fn,
        )
    call_kw = fn.call_kw(ctx, real_model=real_model)
    rpc_call(**call_kw)


@mark.service
def client_feed_factory(peer_registry, rpc_system_call_factory, feed_factory, piece, ctx):
    if isinstance(piece, htypes.model.remote_model):
        _subscribe_remote_feed(peer_registry, rpc_system_call_factory, piece, ctx)
    return feed_factory(piece)
