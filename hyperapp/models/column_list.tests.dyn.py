from unittest.mock import Mock

from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import column_list


@mark.fixture
def lcs():
    lcs = Mock()
    lcs.get.return_value = None
    return lcs


def test_column_list(lcs):
    piece = htypes.column_list.view(
        model_t=pyobj_creg.actor_to_ref(htypes.column_list_tests.sample_model),
        item_t=pyobj_creg.actor_to_ref(htypes.column_list_tests.sample_item),
        )
    items = column_list.column_list(piece, lcs)
    assert len(items) == 3


def test_open():
    adapter = Mock(
        model=htypes.column_list_tests.sample_model(),
        item_t=htypes.column_list_tests.sample_item,
        )
    view = Mock(adapter=adapter)
    piece = column_list.open_column_list(view)
    assert isinstance(piece, htypes.column_list.view)
