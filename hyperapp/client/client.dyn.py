from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    ui_ctl_creg,
    )


def make_layout():
    tabs_layout = htypes.tabs.layout(
        tab_list=[mosaic.put("Nothing is here")],
        )
    window_layout = htypes.window.layout(
        menu_bar_ref=mosaic.put(htypes.menu_bar.menu_bar()),
        command_pane_ref=mosaic.put(htypes.command_pane.command_pane()),
        central_view_ref=mosaic.put(tabs_layout),
        )
    return htypes.application.layout(
        window_list=[mosaic.put(window_layout)],
        )


def make_state():
    tabs_state = htypes.tabs.state(
        current_tab=0,
        )
    window_state = htypes.window.state(
        size=htypes.window.size(200, 100),
        pos=htypes.window.pos(1000, 500),
        central_view_state=mosaic.put(tabs_state),
        )
    return htypes.application.state(
        window_list=[mosaic.put(window_state)],
        )


def _main():
    app = QtWidgets.QApplication()

    layout = make_layout()
    state = make_state()
    app_ctl = ui_ctl_creg.animate(layout)
    window_list = app_ctl.construct_widget(state, ctx=None)
    for window in window_list:
        window.show()

    return app.exec()
