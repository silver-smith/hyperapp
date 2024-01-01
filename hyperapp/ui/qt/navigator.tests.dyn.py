from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    )
from .code.context import Context
from .code.command_hub import CommandHub
from .tested.code import navigator


def _wrapper(diffs):
    return diffs


def test_navigator():
    adapter_layout = htypes.str_adapter.static_str_adapter("Sample text")
    text_layout = htypes.text.view_layout(mosaic.put(adapter_layout))
    layout = htypes.navigator.layout(mosaic.put(text_layout))
    tab_state = htypes.text.state()
    state = htypes.navigator.state(mosaic.put(tab_state))

    app = QtWidgets.QApplication()
    try:
        ctx = Context(command_hub=CommandHub())
        ctl = navigator.NavigatorCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx)
        state = ctl.widget_state(widget)
        assert state
        commands = ctl.get_commands(layout, widget, _wrapper)
        assert commands
    finally:
        app.shutdown()
