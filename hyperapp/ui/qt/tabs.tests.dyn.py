from PySide6 import QtWidgets

from . import htypes
from .tested.code.tabs import TabsCtl, duplicate
from .services import (
    mosaic,
    )
from .code.context import Context


def make_layout():
    return htypes.tabs.layout(
        tab_list=[mosaic.put("Nothing is here")],
        )


def make_state():
    return htypes.tabs.state(
        current_tab=0,
        )


def test_tabs():
    ctx = Context()
    layout = make_layout()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        ctl = TabsCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx)
        state = ctl.widget_state(widget)
        assert state
    finally:
        app.shutdown()


def test_duplicate():
    layout = make_layout()
    state = make_state()
    duplicate(layout, state)
