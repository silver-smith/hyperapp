import logging
import weakref
from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.resource_ctr import add_caller_module_constructor

from . import htypes
from .services import (
    mark,
    mosaic,
    pyobj_creg,
    feed_factory,
    )
from .code.list_diff import ListDiff
from .tested.code import sample_feed

log = logging.getLogger(__name__)


async def test_sample_feed():
    piece = htypes.sample_feed.sample_feed()
    feed = feed_factory(piece)

    await sample_feed.schedule_sample_feed(piece)
    await feed.wait_for_diffs(count=1)

    element_t_res = pyobj_creg.reverse_resolve(htypes.sample_list.item)
    expected_type = htypes.ui.list_feed(mosaic.put(element_t_res))
    log.info("Feed type: %s", feed.type)
    log.info("Expected feed type: %s", expected_type)
    assert feed.type == expected_type
