from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import feed as feed_module


@mark.config_fixture('feed_factory')
def feed_factory_config():
    return {
        htypes.feed_tests.sample_list_feed: feed_module.ListFeed(),
        htypes.feed_tests.sample_index_tree_feed: feed_module.IndexTreeFeed(),
        }


def test_list_feed_factory(feed_factory):
    piece = htypes.feed_tests.sample_list_feed()
    feed = feed_factory(piece)
    assert isinstance(feed, feed_module.ListFeed), repr(feed)


def test_index_tree_feed_factory(feed_factory):
    piece = htypes.feed_tests.sample_index_tree_feed()
    feed = feed_factory(piece)
    assert isinstance(feed, feed_module.IndexTreeFeed), repr(feed)

@mark.fixture
def element_t():
    return pyobj_creg.actor_to_piece(htypes.feed_tests.sample_item)


def test_list_feed_actor(feed_creg, element_t):
    piece = htypes.feed.list_feed_type(mosaic.put(element_t))
    feed = feed_creg.animate(piece)
    assert isinstance(feed, feed_module.ListFeed), repr(feed)


def test_index_tree_feed_actor(feed_creg, element_t):
    piece = htypes.feed.index_tree_feed_type(mosaic.put(element_t))
    feed = feed_creg.animate(piece)
    assert isinstance(feed, feed_module.IndexTreeFeed), repr(feed)
