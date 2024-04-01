from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    )
from .code.context import Context
from .tested.code import box_layout

def make_piece():
    adapter_1 = htypes.str_adapter.static_str_adapter("Sample text 1")
    adapter_2 = htypes.str_adapter.static_str_adapter("Sample text 2")
    text_1 = htypes.text.readonly_view(mosaic.put(adapter_1))
    text_2 = htypes.text.readonly_view(mosaic.put(adapter_2))
    return htypes.box_layout.view(
        direction='LeftToRight',
        elements=[
            htypes.box_layout.element(
                view=mosaic.put(text_1),
                focusable=True,
                stretch=1,
                ),
            htypes.box_layout.element(
                view=mosaic.put(text_2),
                focusable=False,
                stretch=2,
                ),
            ],
        )


def make_state():
    text_state = htypes.text.state()
    return htypes.box_layout.state(
        current=0,
        elements=[
            mosaic.put(text_state),
            mosaic.put(text_state),
            ],
        )


def test_box_layout():
    ctx = Context()
    piece = make_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        view = box_layout.BoxLayoutView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()
