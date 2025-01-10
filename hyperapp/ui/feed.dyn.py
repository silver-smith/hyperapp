import logging
import weakref
from collections import defaultdict

from . import htypes
from .services import (
    deduce_t,
    pyobj_creg,
    )
from .code.mark import mark

log = logging.getLogger(__name__)


class Feed:

    _subscribers = defaultdict(weakref.WeakSet)

    @classmethod
    def from_piece(cls, piece):
        return cls(piece)

    def __init__(self, piece):
        self._piece = piece

    def subscribe(self, subscriber):
        self._subscribers[self._piece].add(subscriber)

    async def send(self, diff):
        log.info("Feed: send: %s", diff)
        for subscriber in self._subscribers.get(self._piece, []):
            subscriber.process_diff(diff)


class ListFeed(Feed):
    pass


class IndexTreeFeed(Feed):
    pass


@mark.actor.feed_creg(htypes.feed.list_feed_type)
def list_feed_from_piece(piece):
    return ListFeed


@mark.actor.feed_creg(htypes.feed.index_tree_feed_type)
def index_tree_feed_from_piece(piece):
    return IndexTreeFeed


@mark.service
def feed_factory(config, piece):
    piece_t = deduce_t(piece)
    feed_type = config[piece_t]
    return feed_type.from_piece(piece)
