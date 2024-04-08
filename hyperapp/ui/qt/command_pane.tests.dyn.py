from PySide6 import QtWidgets

from . import htypes
from .code.context import Context
from .tested.code import command_pane


def test_widget():
    ctx = Context()
    piece = htypes.command_pane.view()
    state = htypes.command_pane.state()
    app = QtWidgets.QApplication()
    try:
        view = command_pane.CommandPaneView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
        view.set_commands(widget, [])
    finally:
        app.shutdown()
