from unittest.mock import Mock

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    )
from .code.context import Context
from .code.list_diff import ListDiff
from .code.view import Diff
from .tested.code import controller


def make_piece():
    adapter_piece = htypes.str_adapter.static_str_adapter("Sample text")
    text_piece = htypes.text.readonly_view(mosaic.put(adapter_piece))
    tabs_piece = htypes.auto_tabs.view(
        tabs=[mosaic.put(text_piece)],
        )
    window_piece = htypes.window.view(
        menu_bar_ref=mosaic.put(htypes.menu_bar.view()),
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
    return htypes.root.state(
        window_list=[mosaic.put(window_state)],
        current=0,
        )


def test_root_view_widget_state():
    ctl = Mock()
    ctl.get_window_state_list.return_value = []
    ctl.window_id_to_idx.return_value = 0
    root_view = controller.RootView(ctl, window_item_id=0)
    state = root_view.widget_state(widget=None)
    assert isinstance(state, htypes.root.state)


def test_apply_root_diff():
    ctx = Context()
    root_piece = make_piece()
    root_state = make_state()
    app = QtWidgets.QApplication()
    try:
        ctl = controller.controller
        ctl.create_windows(root_piece, root_state, ctx, show=False)
        diff = Diff(
            piece=ListDiff.Insert(
                idx=0,
                item=root_piece.window_list[0],
                ),
            state=ListDiff.Insert(
                idx=0,
                item=root_state.window_list[0],
                ),
            )
        ctl._apply_root_diff(diff)
    finally:
        app.shutdown()


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
        parent = htypes.layout.item(1, "Some item", "Item description")
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


async def test_open_view_item_commands():
    piece = htypes.layout.view()
    item = Mock()
    item.id = 123
    result = await controller.open_view_item_commands(piece, current_item=item)
    assert result


def test_view_item_commands():
    ctx = Context()
    root_piece = make_piece()
    root_state = make_state()
    app = QtWidgets.QApplication()
    try:
        controller.controller.create_windows(root_piece, root_state, ctx, show=False)
        piece = htypes.layout.view()
        windows = controller.layout_tree(piece, None)
        window_items = controller.layout_tree(piece, windows[0])
        item_id = window_items[1].id
        commands = controller.view_item_commands(htypes.layout.command_list(item_id))
        assert commands
    finally:
        app.shutdown()


async def test_add_view_command():
    piece = htypes.layout.command_list(item_id=123)
    result = await controller.add_view_command(piece, current_item=None)
