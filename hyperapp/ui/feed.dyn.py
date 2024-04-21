import weakref

from . import htypes
from .services import (
    feed_creg,
    )


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
