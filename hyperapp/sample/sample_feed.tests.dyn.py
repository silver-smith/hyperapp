import logging

from . import htypes
from .services import (
    mark,
    )
from .tested.code import sample_feed

log = logging.getLogger(__name__)


class Feed:

    def send(self, diff):
        log.info("Feed: send: %s", diff)


class FeedDiscoverer:

    def animate(self, piece):
        log.info("Discovered feed piece: %s", piece)
        return Feed()


@mark.service
def feed_creg():
    return FeedDiscoverer()


async def test_sample_feed():
    piece = htypes.sample_feed.sample_feed()
    await sample_feed.schedule_sample_feed(piece)
