from unittest.mock import Mock

from . import htypes
from .tested.code import list_adapter


class ListAdapterStub(list_adapter.FnListAdapterBase):

    def _call_fn(self, **kw):
        pass


def test_colunn_types():
    adapter = ListAdapterStub(
        feed_factory=Mock(),
        lcs=Mock(),
        model=htypes.list_adapter_tests.sample_list(),
        item_t=htypes.list_adapter_tests.item,
        )
    key = adapter._column_d('id')
    assert key
