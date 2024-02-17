from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    )
from .code.context import Context
from .tested.code import controller


def make_piece():
    adapter_piece = htypes.str_adapter.static_str_adapter("Sample text")
    text_piece = htypes.text.view_layout(mosaic.put(adapter_piece))
    tabs_piece = htypes.tabs.layout(
        tabs=[htypes.tabs.tab("One", mosaic.put(text_piece))],
        )
    window_piece = htypes.window.layout(
        menu_bar_ref=mosaic.put(htypes.menu_bar.layout()),
        command_pane_ref=mosaic.put(htypes.command_pane.command_pane()),
        central_view_ref=mosaic.put(tabs_piece),
        )
    return htypes.root.view([
        mosaic.put(window_piece)])


def make_state():
    text_state = htypes.text.state()
    tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=[mosaic.put(text_state)],
        )
    window_state = htypes.window.state(
        menu_bar_state=mosaic.put(htypes.menu_bar.state()),
        central_view_state=mosaic.put(tabs_state),
        size=htypes.window.size(100, 100),
        pos=htypes.window.pos(10, 10),
        )
    return htypes.root.state([
        mosaic.put(window_state)])


def test_layout_tree():
    ctx = Context()
    root_piece = make_piece()
    root_state = make_state()
    app = QtWidgets.QApplication()
    try:
        controller.controller.create_windows(root_piece, root_state, ctx, show=False)
        piece = htypes.layout.view()
        items = controller.layout_tree(piece, None)
        assert items
        parent = htypes.layout.item(1, "Some item")
        controller.layout_tree(piece, parent)
    finally:
        app.shutdown()


def test_layout_tree_commands():
    ctx = Context()
    root_piece = make_piece()
    root_state = make_state()
    app = QtWidgets.QApplication()
    try:
        controller.controller.create_windows(root_piece, root_state, ctx, show=False)
        piece = htypes.layout.view()
        windows = controller.layout_tree(piece, None)
        window_items = controller.layout_tree(piece, windows[0])
        commands = controller.layout_tree_commands(piece, window_items[1])
        assert commands
    finally:
        app.shutdown()
