from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import static_list_adapter



@mark.fixture
def accessor():
    return htypes.accessor.model_accessor()


def test_static_adapter(ui_adapter_creg, accessor):
    ctx = Context()
    model = (
        htypes.list_tests.item(1, "First"),
        htypes.list_tests.item(2, "Second"),
        htypes.list_tests.item(3, "Third"),
        )
    piece = htypes.list_adapter.static_list_adapter(
        item_t=pyobj_creg.actor_to_ref(htypes.list_tests.item),
        accessor=mosaic.put(accessor),
        )
    adapter = ui_adapter_creg.animate(piece, model, ctx)

    assert adapter.column_count() == 2
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'title'

    assert adapter.row_count() == 3
    assert adapter.cell_data(1, 0) == 2
    assert adapter.cell_data(2, 1) == "Third"
