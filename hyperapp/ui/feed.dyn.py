import logging
import weakref

from . import htypes
from .services import (
    deduce_t,
    pyobj_creg,
    )
from .code.mark import mark

log = logging.getLogger(__name__)


class Feed:

    @classmethod
    def from_piece(cls, piece):
        return cls()

    def __init__(self):
        self._subscribers = weakref.WeakSet()

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    async def send(self, diff):
        log.info("Feed: send: %s", diff)
        for subscriber in self._subscribers:
            subscriber.process_diff(diff)


class ListFeed(Feed):
    pass


class IndexTreeFeed(Feed):
    pass


@mark.actor.feed_creg(htypes.ui.list_feed)
def list_feed_from_piece(piece):
    return ListFeed.from_piece(piece)


@mark.actor.feed_creg(htypes.ui.index_tree_feed)
def index_tree_feed_from_piece(piece):
    return IndexTreeFeed.from_piece(piece)


@mark.service2
def feed_factory(config, feed_creg, piece):
    piece_t = deduce_t(piece)
    feed_type = config[piece_t]
    return feed_creg.animate(feed_type)
