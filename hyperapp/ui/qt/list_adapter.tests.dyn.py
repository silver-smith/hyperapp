from unittest.mock import Mock

from . import htypes
from .tested.code.list_adapter import FnListAdapterBase


class ListAdapterStub(FnListAdapterBase):

    def _call_fn(self, **kw):
        pass


def test_colunn_types():
    adapter = ListAdapterStub(
        feed_factory=Mock(),
        column_visible_reg=Mock(),
        model=htypes.list_adapter_tests.sample_list(),
        item_t=htypes.list_adapter_tests.item,
        )
    key = adapter._column_k('id')
    assert key
