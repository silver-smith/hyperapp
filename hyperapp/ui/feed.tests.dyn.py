from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import feed


@mark.config_item_fixture('feed_factory')
def feed_factory_config():
    key = htypes.feed_tests.sample_feed
    element_t = pyobj_creg.actor_to_piece(htypes.feed_tests.sample_item)
    value = htypes.ui.list_feed(
        element_t=mosaic.put(element_t),
        )
    return {key: value}


def test_feed_factory(feed_factory):
    piece = htypes.feed_tests.sample_feed()
    list_feed = feed_factory(piece)
    # TODO: Uncomment when feed_creg actors moved to new services.
    # assert isinstance(list_feed, feed.ListFeed), repr(list_feed)
    list_feed.__class__.__name__ == 'ListFeed'
