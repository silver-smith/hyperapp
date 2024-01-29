from PySide6 import QtWidgets

from . import htypes
from .code.context import Context
from .tested.code import command_hub
from .tested.code import menu_bar


def make_layout():
    return htypes.menu_bar.layout()


def make_state():
    return htypes.menu_bar.state()


def test_widget():
    ctx = Context(command_hub=command_hub.CommandHub())
    piece = make_layout()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        view = menu_bar.MenuBarCtl.from_piece(piece)
        widget = view.construct_widget(piece, state, ctx)
        state = view.widget_state(piece, widget)
        assert state
    finally:
        app.shutdown()
