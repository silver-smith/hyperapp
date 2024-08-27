import asyncio
import inspect
import logging
import weakref

from . import htypes
from .services import (
    deduce_t,
    )
from .code.mark import mark
from .code.list_diff import ListDiff
from .code.tree_diff import TreeDiff
from .code.feed_ctr import ListFeedCtr, IndexTreeFeedCtr

log = logging.getLogger(__name__)


class FeedDiscoverer:

    def __init__(self, ctr_collector, piece_t):
        self._ctr_collector = ctr_collector
        self._piece_t = piece_t
        self.ctr = None
        self._constructor_added = False
        self._subscribers = weakref.WeakSet()
        self._got_diff = asyncio.Condition()
        self._got_diff_count = 0

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    async def send(self, diff):
        log.info("Feed discoverer: send: %s", diff)
        frame = inspect.stack()[1].frame
        python_module_name = frame.f_globals['__name__']
        module_action = self._ctr_collector.get_module_action(python_module_name)
        assert module_action is not self._ctr_collector.Action.NotSet
        if module_action is not self._ctr_collector.Action.Ignore:
            await self._deduce_and_store_ctr(module_action.module_name, diff)
            if self.ctr and not self._constructor_added:
                self._add_constructor()
        for subscriber in self._subscribers:
            subscriber.process_diff(diff)

    async def wait_for_diffs(self, count, timeout=5):
        async with self._got_diff:
            while self._got_diff_count < count:
                async with asyncio.timeout(5):
                    await self._got_diff.wait()

    async def _deduce_and_store_ctr(self, module_name, diff):
        if isinstance(diff, (
                ListDiff.Insert,
                ListDiff.Append,
                ListDiff.Replace,
                )):
            element_t = deduce_t(diff.item)
            ctr = ListFeedCtr(
                module_name=module_name,
                t=self._piece_t,
                element_t=element_t,
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
            if not isinstance(self.ctr, htypes.rc_constructors.list_feed):
                raise RuntimeError(f"Attempt to send different diff types to a feed: {self.ctr} and list diff ({diff})")
        elif isinstance(diff, (
                TreeDiff.Insert,
                TreeDiff.Append,
                TreeDiff.Replace,
                )):
            element_t = deduce_t(diff.item)
            ctr = IndexTreeFeedCtr(
                module_name=module_name,
                t=self._piece_t,
                element_t=element_t,
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
            if not isinstance(self.ctr, htypes.rc_constructors.index_tree_feed):
                raise RuntimeError(f"Attempt to send different diff types to a feed: {self.ctr} and tree diff ({diff})")
        else:
            raise NotImplementedError(f"Not implemented: feed detection for diff: {diff}")
        async with self._got_diff:
            self._got_diff_count += 1
            self._got_diff.notify_all()

    def _add_constructor(self):
        self._ctr_collector.add_constructor(self.ctr)
        self._constructor_added = True


_piece_to_feed = {}


@mark.fixture
def feed_factory(config, ctr_collector, piece):
    log.info("Discovered feed piece: %s", piece)
    try:
        return _piece_to_feed[piece]
    except KeyError:
        pass
    piece_t = deduce_t(piece)
    feed = FeedDiscoverer(ctr_collector, piece_t)
    _piece_to_feed[piece] = feed
    return feed
