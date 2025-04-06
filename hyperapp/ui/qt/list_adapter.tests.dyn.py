from unittest.mock import Mock

from . import htypes
from .tested.code.list_adapter import (
    IndexListAdapterMixin,
    KeyListAdapterMixin,
    FnListAdapterBase,
    )


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


def test_index_list_list_state():
    mixin = IndexListAdapterMixin()
    state = mixin.make_list_state(123)
    assert isinstance(state, htypes.list.state)


def test_key_list_list_state():
    mixin = KeyListAdapterMixin('id', htypes.builtin.string)
    mixin._key_to_idx['some-key'] = 123
    mixin._ensure_populated = lambda: None
    state = mixin.make_list_state('some-key')
    assert isinstance(state, htypes.list.state)
