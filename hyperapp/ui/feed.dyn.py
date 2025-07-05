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

log = logging.getLogger(__name__)


class Feed:

    def __init__(self, piece, on_empty):
        self._piece = piece
        self._on_empty = on_empty
        self._subscribers = weakref.WeakSet()

    def subscribe(self, subscriber):
        # Note: finalize should be called first.
        weakref.finalize(subscriber, self._subscriber_gone)
        self._subscribers.add(subscriber)

    async def send(self, diff):
        log.info("Feed: send: %s", diff)
        for subscriber in self._subscribers:
            subscriber.process_diff(diff)

    def _subscriber_gone(self):
        if not self._subscribers:
            self._on_empty(self._piece)


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


@mark.service
def feed_factory(config, feed_map, piece):
    try:
        return feed_map[piece]
    except KeyError:
        pass

    def on_empty(piece):
        del feed_map[piece]

    if isinstance(piece, htypes.model.remote_model):
        real_model = web.summon(piece.model)
    else:
        real_model = piece

    model_t = deduce_t(real_model)
    Feed = config[model_t]
    feed = Feed(piece, on_empty)
    feed_map[piece] = feed
    return feed
