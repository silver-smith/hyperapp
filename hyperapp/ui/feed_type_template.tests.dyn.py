from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import feed_type_template


@mark.fixture
def template_piece():
    feed_type_piece = htypes.feed.list_feed_type(
        item_t=pyobj_creg.actor_to_ref(htypes.feed_type_template_tests.sample_item),
        )
    return htypes.feed.feed_template(
        feed_type=mosaic.put(feed_type_piece),
        )


def test_cfg_value(system, template_piece):
    key = '<unused>'
    feed_type = feed_type_template.resolve_feed_type_cfg_value(template_piece, key, system, '<unused-service-name>')
