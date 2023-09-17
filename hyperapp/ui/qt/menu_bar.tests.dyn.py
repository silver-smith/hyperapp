from PySide6 import QtWidgets

from . import htypes
from .tested.code.menu_bar import MenuBarCtl


def make_layout():
    return htypes.menu_bar.layout()


def make_state():
    return htypes.menu_bar.state()


def test_widget():
    layout = make_layout()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        ctl = MenuBarCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx=None)
    finally:
        app.shutdown()
