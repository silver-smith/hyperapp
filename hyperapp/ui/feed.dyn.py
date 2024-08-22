import logging
import weakref

from hyperapp.common.htypes.deduce_value_type import deduce_value_type

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    feed_creg,
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


@feed_creg.actor(htypes.ui.list_feed)
def list_feed_from_piece(piece):
    return ListFeed.from_piece(piece)


@feed_creg.actor(htypes.ui.index_tree_feed)
def index_tree_feed_from_piece(piece):
    return IndexTreeFeed.from_piece(piece)


@mark.service2
def feed_factory(config, piece):
    piece_t = deduce_value_type(piece)
    feed_type = config[piece_t]
    return feed_creg.animate(feed_type)
