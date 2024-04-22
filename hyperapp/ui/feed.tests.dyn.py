from . import htypes
from .services import (
    mark,
    mosaic,
    pyobj_creg,
    )
from .tested.code import feed
from .tested.services import feed_factory


class PhonyAssociationRegistry:

    def __getitem__(self, key):
        element_t = pyobj_creg.reverse_resolve(htypes.feed_tests.sample_item)
        return htypes.ui.list_feed(
            element_t=mosaic.put(element_t),
            )


@mark.service
def association_reg():
    return PhonyAssociationRegistry()


def test_feed_factory():
    piece = htypes.feed_tests.sample_feed()
    list_feed = feed_factory(piece)
    assert isinstance(list_feed, feed.ListFeed)
