import asyncio

from PySide6 import QtWidgets
from qasync import QEventLoop

from . import htypes
from .services import (
    mosaic,
    visualizer,
    ui_ctl_creg,
    )
from .code.context import Context


def make_layout():
    text = "Sample text"
    view_layout = visualizer(text)
    navigator_layout = htypes.navigator.layout(mosaic.put(view_layout))
    inner_tabs_layout = htypes.tabs.layout(
        tabs=[
            htypes.tabs.tab("Inner", mosaic.put(navigator_layout)),
            ],
        )
    outer_tabs_layout = htypes.tabs.layout(
        tabs=[
            htypes.tabs.tab("Outer", mosaic.put(inner_tabs_layout)),
            ],
        )
    window_layout = htypes.window.layout(
        menu_bar_ref=mosaic.put(htypes.menu_bar.layout()),
        command_pane_ref=mosaic.put(htypes.command_pane.command_pane()),
        central_view_ref=mosaic.put(outer_tabs_layout),
        )
    return htypes.application.layout(
        window_list=[mosaic.put(window_layout)],
        )


def make_state():
    text_state = htypes.text.state()
    navigator_state = htypes.navigator.state(mosaic.put(text_state))
    inner_tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=[mosaic.put(navigator_state)],
        )
    outer_tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=[mosaic.put(inner_tabs_state)],
        )
    window_state = htypes.window.state(
        menu_bar_state=mosaic.put(htypes.menu_bar.state()),
        central_view_state=mosaic.put(outer_tabs_state),
        size=htypes.window.size(500, 300),
        pos=htypes.window.pos(1000, 500),
        )
    return htypes.application.state(
        window_list=[mosaic.put(window_state)],
        )


def _main():
    app = QtWidgets.QApplication()
    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)  # Should be set before any asyncio objects created.

    ctx = Context()
    layout = make_layout()
    state = make_state()
    app_ctl = ui_ctl_creg.animate(layout)
    window_list = app_ctl.construct_widget(state, ctx)
    for window in window_list:
        window.show()

    return app.exec()
