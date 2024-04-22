import logging
import weakref

from hyperapp.common.htypes.deduce_value_type import deduce_value_type

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    feed_creg,
    mark,
    pyobj_creg,
    )

log = logging.getLogger(__name__)


class ListFeed:

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


@feed_creg.actor(htypes.ui.list_feed)
def list_feed_from_piece(piece):
    return ListFeed.from_piece(piece)


class FeedFactory:

    def __call__(self, piece):
        piece_t = deduce_value_type(piece)
        piece_t_res = pyobj_creg.reverse_resolve(piece_t)
        feed_d_res = data_to_res(htypes.ui.feed_d())
        feed_type = association_reg[feed_d_res, piece_t_res]
        return feed_creg.animate(feed_type)
        

@mark.service
def feed_factory():
    return FeedFactory()
