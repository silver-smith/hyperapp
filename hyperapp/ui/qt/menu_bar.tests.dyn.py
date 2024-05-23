from unittest.mock import Mock


from PySide6 import QtWidgets

from . import htypes
from .code.context import Context
from .tested.code import menu_bar


def make_piece():
    return htypes.menu_bar.view()


def make_state():
    return htypes.menu_bar.state()


def test_widget():
    ctx = Context()
    piece = make_piece()
    state = make_state()
    command = Mock(groups=set(), enabled=True, shortcut="")
    command.name = "Sample"
    app = QtWidgets.QApplication()
    try:
        view = menu_bar.MenuBarView.from_piece(piece, ctx)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
        view.set_commands(widget, [command])
    finally:
        app.shutdown()
