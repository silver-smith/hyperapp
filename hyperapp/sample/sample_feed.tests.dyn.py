import asyncio
import logging
import weakref
from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.resource_ctr import add_caller_module_constructor
from . import htypes
from .services import (
    mark,
    mosaic,
    pyobj_creg,
    )
from .code.list_diff import ListDiff
from .tested.code import sample_feed

log = logging.getLogger(__name__)


class Feed:

    def __init__(self, piece_t):
        self._piece_t = piece_t
        self.type = None
        self._subscribers = weakref.WeakSet()

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    def send(self, diff):
        log.info("Feed: send: %s", diff)
        self._deduce_and_store_type(diff)
        if self.type:
            piece_t_res = pyobj_creg.reverse_resolve(self._piece_t)
            ctr = htypes.rc_constructors.list_feed_ctr(
                t=mosaic.put(piece_t_res),
                element_t=self.type.element_t,
                )
            add_caller_module_constructor(2, mosaic.put(ctr))
        for subscriber in self._subscribers:
            subscriber(diff)

    def _deduce_and_store_type(self, diff):
        if isinstance(diff, (
                ListDiff.Insert,
                ListDiff.Append,
                ListDiff.Replace,
                )):
            element_t = deduce_value_type(diff.item)
            element_t_res = pyobj_creg.reverse_resolve(element_t)
            feed = htypes.ui.list_feed(mosaic.put(element_t_res))
            if self.type:
                if feed != self.type:
                    raise RuntimeError(f"Attempt to send different diff types to a feed: {self.type} and {feed}")
            else:
                self.type = feed
                log.info("Feed: Deduced feed type: %s [%s]", self.type, element_t)
            return
        if self.type and isinstance(diff, (
                ListDiff.Remove,
                ListDiff.Modify,
                )):
            if not isinstance(self.type, htypes.ui.list_feed):
                raise RuntimeError(f"Attempt to send different diff types to a feed: {self.type} and list diff ({diff})")
            return
        raise NotImplementedError(f"Not implemented: feed detection for diff: {diff}")


class FeedDiscoverer:

    def __init__(self):
        self._piece_to_feed = {}

    def animate(self, piece):
        log.info("Discovered feed piece: %s", piece)
        try:
            return self._piece_to_feed[piece]
        except KeyError:
            pass
        piece_t = deduce_value_type(piece)
        feed = Feed(piece_t)
        self._piece_to_feed[piece] = feed
        return feed


_feed_discoverer = FeedDiscoverer()


@mark.service
def feed_creg():
    return _feed_discoverer


async def test_sample_feed():
    piece = htypes.sample_feed.sample_feed()

    feed = _feed_discoverer.animate(piece)
    event = asyncio.Event()

    def on_diff(diff):
        event.set()

    feed.subscribe(on_diff)
    await sample_feed.schedule_sample_feed(piece)

    async with asyncio.timeout(5):
        await event.wait()

    element_t_res = pyobj_creg.reverse_resolve(htypes.sample_list.item)
    expected_type = htypes.ui.list_feed(mosaic.put(element_t_res))
    log.info("Feed type: %s", feed.type)
    log.info("Expected feed type: %s", expected_type)
    assert feed.type == expected_type
