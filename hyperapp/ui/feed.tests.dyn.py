from unittest.mock import Mock

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
        htypes.feed_tests.sample_list_feed: feed_module.ListFeed,
        htypes.feed_tests.sample_index_tree_feed: feed_module.IndexTreeFeed,
        }


def test_list_feed_factory(feed_factory):
    piece = htypes.feed_tests.sample_list_feed()
    feed = feed_factory(piece)
    assert isinstance(feed, feed_module.ListFeed), repr(feed)


def test_index_tree_feed_factory(feed_factory):
    piece = htypes.feed_tests.sample_index_tree_feed()
    feed = feed_factory(piece)
    assert isinstance(feed, feed_module.IndexTreeFeed), repr(feed)


class SampleSubscriber:
    pass


def test_feed_finalizer(feed_map, feed_factory):
    piece = htypes.feed_tests.sample_list_feed()
    feed = feed_factory(piece)
    subscriber = Mock()
    feed.subscribe(subscriber)
    assert piece in feed_map
    del subscriber
    assert piece not in feed_map


@mark.fixture
def item_t():
    return pyobj_creg.actor_to_piece(htypes.feed_tests.sample_item)


def test_list_feed_actor(feed_type_creg, item_t):
    piece = htypes.feed.list_feed_type(mosaic.put(item_t))
    feed_type = feed_type_creg.animate(piece)
    assert feed_type is feed_module.ListFeed, repr(feed_type)


def test_index_tree_feed_actor(feed_type_creg, item_t):
    piece = htypes.feed.index_tree_feed_type(mosaic.put(item_t))
    feed_type = feed_type_creg.animate(piece)
    assert feed_type is feed_module.IndexTreeFeed, repr(feed_type)


def test_value_feed_actor(item_t):
    piece = htypes.feed.value_feed_type(
        value_t=mosaic.put(item_t),
        )
    feed_type = feed_module.value_feed_from_piece(piece)
    assert feed_type is feed_module.ValueFeed, repr(feed_type)
