from PySide6 import QtWidgets

from . import htypes
from .services import (
    fn_to_res,
    mosaic,
    )
from .code.context import Context
from .tested.code import master_details


def _details_command(piece):
    return f"Details for: {piece}"


def make_piece():
    model = "Sample master text"
    master_adapter = htypes.str_adapter.static_str_adapter(model)
    details_adapter= htypes.str_adapter.static_str_adapter("Sample details")
    master = htypes.text.view_layout(mosaic.put(master_adapter))
    details = htypes.text.view_layout(mosaic.put(details_adapter))
    command = htypes.ui.model_command(
        function=mosaic.put(fn_to_res(_details_command)),
        params=['piece'],
        )
    return htypes.master_details.view(
        model=mosaic.put(model),
        master_view=mosaic.put(master),
        details_command=mosaic.put(command),
        details_view=mosaic.put(details),
        direction='LeftToRight',
        master_stretch=1,
        details_stretch=1,
        )


def make_state():
    text_state = htypes.text.state()
    return htypes.master_details.state(
        master_state=(mosaic.put(text_state)),
        details_state=(mosaic.put(text_state)),
        )


def test_box_layout():
    ctx = Context()
    piece = make_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        view = master_details.MasterDetailsView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()
