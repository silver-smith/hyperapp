from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import wiki_refs


@mark.fixture
def accessor():
    return htypes.accessor.model_accessor()


@mark.fixture
def adapter_piece(accessor):
    return htypes.wiki.ref_list_adapter(
        accessor=mosaic.put(accessor),
        )


@mark.fixture
def sample_ref_target():
    return mosaic.put('sample-ref-value')


@mark.fixture
def model(sample_ref_target):
    return htypes.wiki.wiki(
        text="Sample text",
        refs=(
          htypes.wiki.wiki_ref('abc', sample_ref_target),
          ),
        )


@mark.fixture
def ctx(model):
    return Context(
        model=model,
        )


def test_adapter(adapter_piece, model, ctx):
    adapter = wiki_refs.WikiRefListAdapter.from_piece(adapter_piece, model, ctx)
    assert adapter.cell_data(0, 0) == 'abc'
    assert adapter.cell_data(0, 2) == 'sample-ref-value', adapter.cell_data(0, 2)
    current_idx = 0
    current_item = adapter.get_item(current_idx)
    model_state = adapter.make_model_state(current_idx, current_item)
    assert isinstance(model_state, htypes.wiki.ref_list_model_state)


def test_view_factory(accessor):
    piece = wiki_refs.wiki_refs(accessor)
    assert isinstance(piece, htypes.list.view)
