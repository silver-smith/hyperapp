from PySide6 import QtWidgets

from . import htypes
from .code.context import Context
from .tested.code import menu_bar


def make_layout():
    return htypes.menu_bar.layout()


def make_state():
    return htypes.menu_bar.state()


def test_widget():
    ctx = Context({'commands': []})
    layout = make_layout()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        ctl = menu_bar.MenuBarCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx)
    finally:
        app.shutdown()
