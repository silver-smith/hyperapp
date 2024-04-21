import asyncio
import logging
import weakref

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.resource_ctr import add_caller_module_constructor

from . import htypes
from .services import (
    mark,
    mosaic,
    pyobj_creg,
    )
from .services import feed_creg as true_feed_creg
from .code.list_diff import ListDiff

log = logging.getLogger(__name__)


class Feed:

    def __init__(self, piece_t):
        self._piece_t = piece_t
        self.type = None
        self._constructor_added = False
        self._subscribers = weakref.WeakSet()
        self._got_diff = asyncio.Condition()
        self._got_diff_count = 0

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    async def send(self, diff):
        log.info("Feed fixture: send: %s", diff)
        await self._deduce_and_store_type(diff)
        if self.type and not self._constructor_added:
            piece_t_res = pyobj_creg.reverse_resolve(self._piece_t)
            ctr = htypes.rc_constructors.list_feed_ctr(
                t=mosaic.put(piece_t_res),
                element_t=self.type.element_t,
                )
            add_caller_module_constructor(2, mosaic.put(ctr))
            self._constructor_added = True
        for subscriber in self._subscribers:
            subscriber(diff)

    async def wait_for_diffs(self, count, timeout=5):
        async with self._got_diff:
            while self._got_diff_count < count:
                async with asyncio.timeout(5):
                    await self._got_diff.wait()

    async def _deduce_and_store_type(self, diff):
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
        elif self.type and isinstance(diff, (
                ListDiff.Remove,
                ListDiff.Modify,
                )):
            if not isinstance(self.type, htypes.ui.list_feed):
                raise RuntimeError(f"Attempt to send different diff types to a feed: {self.type} and list diff ({diff})")
        else:
            raise NotImplementedError(f"Not implemented: feed detection for diff: {diff}")
        async with self._got_diff:
            self._got_diff_count += 1
            self._got_diff.notify_all()


class FeedDiscoverer:

    def __init__(self):
        self._piece_to_feed = {}

    def actor(self, t):
        return true_feed_creg.actor(t)

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


@mark.service
def feed_creg():
    return FeedDiscoverer()
