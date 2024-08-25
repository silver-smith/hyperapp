import logging

from . import htypes
from .code.feed_ctr import ListFeedCtr, IndexTreeFeedCtr
from .fixtures import feed_fixtures
from .tested.code import sample_feed

log = logging.getLogger(__name__)


async def test_sample_list_feed(feed_factory):
    piece = htypes.sample_feed.sample_list_feed()
    feed = feed_factory(piece)

    await sample_feed.schedule_sample_list_feed(feed_factory, piece)
    await feed.wait_for_diffs(count=1)

    assert isinstance(feed.ctr, ListFeedCtr)


async def test_sample_tree_feed(feed_factory):
    piece = htypes.sample_feed.sample_tree_feed()
    feed = feed_factory(piece)

    await sample_feed.schedule_sample_tree_feed(feed_factory, piece)
    await feed.wait_for_diffs(count=1)

    assert isinstance(feed.ctr, IndexTreeFeedCtr)
