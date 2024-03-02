from PySide6 import QtWidgets

from . import htypes
from .code.context import Context
from .code import command_hub
from .tested.code import command_pane


def test_widget():
    ctx = Context(command_hub=command_hub.CommandHub())
    piece = htypes.command_pane.view()
    state = htypes.command_pane.state()
    app = QtWidgets.QApplication()
    try:
        view = command_pane.CommandPaneView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
        view.commands_changed(widget, [], [])
    finally:
        app.shutdown()
