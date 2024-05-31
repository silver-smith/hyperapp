from unittest.mock import Mock

from PySide6 import QtWidgets

from hyperapp.common.htypes import tInt

from . import htypes
from .services import (
    fn_to_ref,
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
from .tested.code import form


def _sample_form_fn(piece):
    assert isinstance(piece, htypes.form_tests.sample_form), repr(piece)
    return htypes.form_tests.item(123, "Sample  item")


def _make_adapter_piece():
    item_t_res = pyobj_creg.reverse_resolve(htypes.form_tests.item)
    return htypes.record_adapter.fn_record_adapter(
        record_t=mosaic.put(item_t_res),
        function=fn_to_ref(_sample_form_fn),
        params=('piece',),
        )


def _make_piece():
    adapter_piece = _make_adapter_piece()
    return htypes.form.view(mosaic.put(adapter_piece))


def _make_lcs():
    lcs = Mock()
    # Fall thru to default layout.
    lcs.get.return_value = None
    return lcs


def test_form():
    lcs = _make_lcs()
    ctx = Context(lcs=lcs)
    piece = _make_piece()
    model = htypes.form_tests.sample_form()
    state = None
    app = QtWidgets.QApplication()
    try:
        view = form.FormView.from_piece(piece, model, ctx)
        view.set_controller_hook(Mock())
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
        assert hash(state)  # Check it is hashable.
        assert view.get_model() == model
        model_state = view.model_state(widget)
        # assert model_state
    finally:
        app.shutdown()
