import asyncio

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
    prev_layout = htypes.navigator.layout(
        current_layout=mosaic.put(text_layout),
        prev=None,
        next=None,
        )
    layout = htypes.navigator.layout(
        current_layout=mosaic.put(text_layout),
        prev=mosaic.put(prev_layout),
        next=None,
        )
    tab_state = htypes.text.state()
    state = htypes.navigator.state(
        current_state=mosaic.put(tab_state),
        prev=None,
        next=None,
        )

    app = QtWidgets.QApplication()
    try:
        ctx = Context(command_hub=CommandHub())
        ctl = navigator.NavigatorCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx)
        state = ctl.widget_state(widget)
        assert state
        command_list = ctl.get_commands(layout, widget, _wrapper)
        assert command_list
        for command in command_list:
            layout_diff, state_diff = asyncio.run(command.run())
            ctl.apply(ctx, widget, layout_diff, state_diff)
    finally:
        app.shutdown()
