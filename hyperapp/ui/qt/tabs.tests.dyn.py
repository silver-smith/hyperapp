from PySide6 import QtWidgets

from . import htypes
from .tested.code import tabs
from .services import (
    mosaic,
    )
from .code.context import Context


def make_layout():
    text_layout = htypes.text.layout()
    return htypes.tabs.layout(
        tabs=[
            htypes.tabs.tab("One", mosaic.put(text_layout))],
        )


def make_state():
    text_state = htypes.text.state("Some text")
    return htypes.tabs.state(
        current_tab=0,
        tabs=[mosaic.put(text_state)],
        )


def test_tabs():
    ctx = Context()
    layout = make_layout()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        ctl = tabs.TabsCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx)
        state = ctl.widget_state(widget)
        assert state
    finally:
        app.shutdown()


def test_duplicate():
    ctx = Context()
    layout = make_layout()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        ctl = tabs.TabsCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx)
        layout_diff, state_diff = tabs.duplicate(layout, state)
        new_layout = ctl.apply(widget, layout_diff, state_diff)
        assert len(new_layout.tabs) == 2
        assert new_layout.tabs[0] == layout.tabs[0]
        assert new_layout.tabs[0] == new_layout.tabs[1]
    finally:
        app.shutdown()
