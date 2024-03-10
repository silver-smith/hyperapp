from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    )
from .code.context import Context
from .code.command_hub import CommandHub
from .tested.code import tab_groups


def make_piece():
    adapter = htypes.str_adapter.static_str_adapter("Sample text")
    text = htypes.text.readonly_view(mosaic.put(adapter))
    return htypes.tab_groups.view([
        htypes.tabs.tab("One", mosaic.put(text)),
        ])


def make_state():
    text_state = htypes.text.state()
    return htypes.tabs.state(
        current_tab=0,
        tabs=[mosaic.put(text_state)],
        )


def test_tabs():
    ctx = Context(command_hub=CommandHub())
    piece = make_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        view = tab_groups.TabGroupsView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()
