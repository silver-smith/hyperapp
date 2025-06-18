from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .tested.code import feed_type_template


def test_feed_type_template(system):
    piece_t = htypes.feed_type_template_tests.sample_view
    feed_type_piece = htypes.feed.list_feed_type(
        item_t=pyobj_creg.actor_to_ref(htypes.feed_type_template_tests.sample_item),
        )
    template_piece = htypes.feed.feed_template(
        model_t=pyobj_creg.actor_to_ref(piece_t),
        feed_type=mosaic.put(feed_type_piece),
        )
    key, piece = feed_type_template.resolve_feed_type_cfg_item(template_piece)
    assert key == piece_t
    feed_type = feed_type_template.resolve_feed_type_cfg_value(template_piece, key, system, '<unused-service-name>')
