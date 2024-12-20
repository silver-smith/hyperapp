from unittest.mock import Mock

from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.mark import mark
from .fixtures import feed_fixtures
from .tested.code import column_list


@mark.fixture
def lcs():
    def mock_get(key, default=None):
        return default
    lcs = Mock()
    lcs.get = mock_get
    return lcs


@mark.fixture
def piece():
    return htypes.column_list.view(
        model_t=pyobj_creg.actor_to_ref(htypes.column_list_tests.sample_model),
        item_t=pyobj_creg.actor_to_ref(htypes.column_list_tests.sample_item),
        )


def test_column_list(lcs, piece):
    items = column_list.column_list(piece, lcs)
    assert len(items) == 3


async def test_toggle_visibility(feed_factory, lcs, piece):
    feed = feed_factory(piece)
    current_idx = 0
    current_item = htypes.column_list.item(
        name='id',
        show=False,  # Should not be used.
        )
    await column_list.toggle_visibility(piece, current_idx, current_item, lcs)
    lcs.set.assert_called_once()
    assert lcs.set.call_args.args[1] == False
    await feed.wait_for_diffs(count=1)


def test_open():
    adapter = Mock(
        model=htypes.column_list_tests.sample_model(),
        item_t=htypes.column_list_tests.sample_item,
        )
    view = Mock(adapter=adapter)
    piece = column_list.open_column_list(view)
    assert isinstance(piece, htypes.column_list.view)
