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


def make_default_piece():
    adapter_piece = htypes.str_adapter.static_str_adapter("Sample text")
    text_piece = htypes.text.readonly_view(mosaic.put(adapter_piece))
    tabs_piece = htypes.auto_tabs.view(
        tabs=(mosaic.put(text_piece),),
        )
    window_piece = htypes.window.view(
        menu_bar_ref=mosaic.put(htypes.menu_bar.view()),
        central_view_ref=mosaic.put(tabs_piece),
        )
    return htypes.root.view((
        mosaic.put(window_piece),
        ))


def make_default_state():
    text_state = htypes.text.state()
    tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(text_state),),
        )
    window_state = htypes.window.state(
        menu_bar_state=mosaic.put(htypes.menu_bar.state()),
        central_view_state=mosaic.put(tabs_state),
        size=htypes.window.size(100, 100),
        pos=htypes.window.pos(10, 10),
        )
    return htypes.root.state(
        window_list=(mosaic.put(window_state),),
        current=0,
        )


def make_default_layout():
    return htypes.root.layout(
        piece=make_default_piece(),
        state=make_default_state(),
        )


class PhonyLayoutBundle:

    def load_piece(self):
        raise FileNotFoundError("Phony layout bundle")

    def save_piece(self, piece):
        pass


# Visit htypes.root.state type.
def test_root_view_widget_state():
    item = Mock(id=0)
    item.view.widget_state.return_value = 'mock widget state'
    root_view = controller.RootView([item], window_item_id=0)
    state = root_view.widget_state(widget=None)
    assert isinstance(state, htypes.root.state)


def test_apply_root_diff():
    ctx = Context()
    default_layout = make_default_layout()
    app = QtWidgets.QApplication()
    try:
        with controller.Controller.running(PhonyLayoutBundle(), default_layout, ctx) as ctl:
            diff = Diff(
                piece=ListDiff.Insert(
                    idx=0,
                    item=default_layout.piece.window_list[0],
                    ),
                state=ListDiff.Insert(
                    idx=0,
                    item=default_layout.state.window_list[0],
                    ),
                )
            ctl._root_item.children[0]._apply_diff(diff)
    finally:
        app.shutdown()


def test_layout_tree():
    ctx = Context()
    default_layout = make_default_layout()
    app = QtWidgets.QApplication()
    try:
        with controller.Controller.running(PhonyLayoutBundle(), default_layout, ctx):
            piece = htypes.layout.view()
            items = controller.layout_tree(piece, None)
            assert items
            parent = htypes.layout.item(1, "Some item", True, "Item description")
            controller.layout_tree(piece, parent)
    finally:
        app.shutdown()


def test_layout_tree_commands():
    ctx = Context()
    default_layout = make_default_layout()
    app = QtWidgets.QApplication()
    try:
        with controller.Controller.running(PhonyLayoutBundle(), default_layout, ctx):
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
    default_layout = make_default_layout()
    app = QtWidgets.QApplication()
    try:
        with controller.Controller.running(PhonyLayoutBundle(), default_layout, ctx):
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
