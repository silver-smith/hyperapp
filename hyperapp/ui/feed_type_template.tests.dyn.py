from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .tested.code import feed_type_template


def test_feed_type_template():
    piece_t = htypes.feed_type_template_tests.sample_view
    feed_type = htypes.feed.list_feed_type(
        item_t=pyobj_creg.actor_to_ref(htypes.feed_type_template_tests.sample_item),
        )
    template_piece = htypes.feed.feed_template(
        t=pyobj_creg.actor_to_ref(piece_t),
        feed_type=mosaic.put(feed_type),
        )
    template = feed_type_template.FeedTypeTemplate.from_piece(template_piece)
    assert template.piece == template_piece
