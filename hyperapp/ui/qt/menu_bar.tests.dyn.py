from PySide6 import QtWidgets

from . import htypes
from .code.context import Context
from .code import command_hub
from .tested.code import menu_bar


def make_piece():
    return htypes.menu_bar.view()


def make_state():
    return htypes.menu_bar.state()


def test_widget():
    ctx = Context(command_hub=command_hub.CommandHub())
    piece = make_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        view = menu_bar.MenuBarView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()
