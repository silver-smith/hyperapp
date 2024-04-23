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
from .code.list_diff import ListDiff
from .code.tree_diff import TreeDiff

log = logging.getLogger(__name__)


class FeedDiscoverer:

    def __init__(self, piece_t):
        self._piece_t = piece_t
        self.ctr = None
        self._constructor_added = False
        self._subscribers = weakref.WeakSet()
        self._got_diff = asyncio.Condition()
        self._got_diff_count = 0
        self._piece_t_res = pyobj_creg.reverse_resolve(self._piece_t)

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    async def send(self, diff):
        log.info("Feed discoverer: send: %s", diff)
        await self._deduce_and_store_ctr(diff)
        if self.ctr and not self._constructor_added:
            add_caller_module_constructor(2, mosaic.put(self.ctr))
            self._constructor_added = True
        for subscriber in self._subscribers:
            subscriber.process_diff(diff)

    async def wait_for_diffs(self, count, timeout=5):
        async with self._got_diff:
            while self._got_diff_count < count:
                async with asyncio.timeout(5):
                    await self._got_diff.wait()

    async def _deduce_and_store_ctr(self, diff):
        if isinstance(diff, (
                ListDiff.Insert,
                ListDiff.Append,
                ListDiff.Replace,
                )):
            element_t = deduce_value_type(diff.item)
            element_t_res = pyobj_creg.reverse_resolve(element_t)
            ctr = htypes.rc_constructors.list_feed_ctr(
                t=mosaic.put(self._piece_t_res),
                element_t=mosaic.put(element_t_res),
                )
            if self.ctr:
                if ctr != self.ctr:
                    raise RuntimeError(f"Attempt to send different diff types to a feed: {self.ctr} and {ctr}")
            else:
                self.ctr = ctr
                log.info("Feed: Deduced feed type: %s [%s]", self.ctr, element_t)
        elif self.ctr and isinstance(diff, (
                ListDiff.Remove,
                ListDiff.Modify,
                )):
            if not isinstance(self.ctr, htypes.rc_constructors.list_feed_ctr):
                raise RuntimeError(f"Attempt to send different diff types to a feed: {self.ctr} and list diff ({diff})")
        elif isinstance(diff, (
                TreeDiff.Insert,
                TreeDiff.Append,
                TreeDiff.Replace,
                )):
            element_t = deduce_value_type(diff.item)
            element_t_res = pyobj_creg.reverse_resolve(element_t)
            ctr = htypes.rc_constructors.index_tree_feed_ctr(
                t=mosaic.put(self._piece_t_res),
                element_t=mosaic.put(element_t_res),
                )
            if self.ctr:
                if ctr != self.ctr:
                    raise RuntimeError(f"Attempt to send different diff types to a feed: {self.ctr} and {feed}")
            else:
                self.ctr = ctr
                log.info("Feed: Deduced feed type: %s [%s]", self.ctr, element_t)
        elif self.ctr and isinstance(diff, (
                TreeDiff.Remove,
                TreeDiff.Modify,
                )):
            if not isinstance(self.ctr, htypes.rc_constructors.index_tree_feed_ctr):
                raise RuntimeError(f"Attempt to send different diff types to a feed: {self.ctr} and tree diff ({diff})")
        else:
            raise NotImplementedError(f"Not implemented: feed detection for diff: {diff}")
        async with self._got_diff:
            self._got_diff_count += 1
            self._got_diff.notify_all()


class FeedDiscovererFactory:

    def __init__(self):
        self._piece_to_feed = {}

    def __call__(self, piece):
        log.info("Discovered feed piece: %s", piece)
        try:
            return self._piece_to_feed[piece]
        except KeyError:
            pass
        piece_t = deduce_value_type(piece)
        feed = FeedDiscoverer(piece_t)
        self._piece_to_feed[piece] = feed
        return feed


@mark.service
def feed_factory():
    return FeedDiscovererFactory()
