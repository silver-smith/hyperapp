from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    ui_ctl_creg,
    )


def make_window_layout():
    return htypes.window.layout(
        menu_bar_ref=mosaic.put(htypes.menu_bar.menu_bar()),
        command_pane_ref=mosaic.put(htypes.command_pane.command_pane()),
        central_view_ref=mosaic.put('phony view'),
        )


def make_window_state():
    return htypes.window.state(
        size=htypes.window.size(200, 100),
        pos=htypes.window.pos(1000, 500),
        )


def _main():
    app = QtWidgets.QApplication()

    window_layout = make_window_layout()
    window_state = make_window_state()
    window_ctl = ui_ctl_creg.animate(window_layout)
    window = window_ctl.construct_widget(window_state, ctx=None)
    window.show()

    return app.exec()
