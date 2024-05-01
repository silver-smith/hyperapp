from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    )
from .code.context import Context
from .tested.code import box_layout

def make_piece():
    label_1 = htypes.label.view("Sample label 1")
    label_2 = htypes.label.view("Sample label 2")
    return htypes.box_layout.view(
        direction='LeftToRight',
        elements=[
            htypes.box_layout.element(
                view=mosaic.put(label_1),
                focusable=True,
                stretch=1,
                ),
            htypes.box_layout.element(
                view=mosaic.put(label_2),
                focusable=False,
                stretch=2,
                ),
            ],
        )


def make_state():
    label_state = htypes.label.state()
    return htypes.box_layout.state(
        current=0,
        elements=[
            mosaic.put(label_state),
            mosaic.put(label_state),
            ],
        )


def test_box_layout():
    ctx = Context()
    piece = make_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        view = box_layout.BoxLayoutView.from_piece(piece, ctx)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()
