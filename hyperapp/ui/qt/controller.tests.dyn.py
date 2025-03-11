from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import feed_fixtures
from .fixtures import qapp_fixtures
from .tested.code import controller
from .tested.code import window_commands


@mark.fixture
def default_piece():
    adapter = htypes.str_adapter.static_str_adapter()
    text = htypes.text.readonly_view(mosaic.put(adapter))
    navigator = htypes.navigator.view(
        current_view=mosaic.put(text),
        current_model=mosaic.put("Sample model"),
        layout_k=None,
        prev=None,
        next=None,
        )
    tabs_piece = htypes.auto_tabs.view(
        tabs=(htypes.tabs.tab("One", mosaic.put(navigator)),),
        )
    window_piece = htypes.window.view(
        menu_bar_ref=mosaic.put(htypes.menu_bar.view()),
        central_view_ref=mosaic.put(tabs_piece),
        )
    return htypes.root.view((
        mosaic.put(window_piece),
        ))


@mark.fixture
def default_state():
    text_state = htypes.text.state('')
    navigator_state = text_state
    tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(navigator_state),),
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


@mark.fixture
def default_layout(default_piece, default_state):
    return htypes.root.layout(
        piece=default_piece,
        state=default_state,
        )


class PhonyLayoutBundle:

    def load_piece(self):
        raise FileNotFoundError("Phony layout bundle")

    def save_piece(self, piece):
        pass


def test_canned_ctl_item_factory():
    ctl = Mock()
    piece = htypes.ui.canned_ctl_item(
        item_id=123,
        path=(0, 1),
        )
    ctx = Context(
        controller=ctl,
        )
    mock_item = controller.canned_ctl_item_factory(piece, ctx)


async def test_controller_and_duplicate_window(
        qapp, feed_factory, canned_ctl_item_factory, controller_running, default_layout):
    lcs = Mock()
    lcs.get.return_value = None  # command list - mock is not iterable.
    ctx = Context(lcs=lcs)
    feed = feed_factory(htypes.layout.view())

    async with controller_running(PhonyLayoutBundle(), default_layout, ctx, show=False, load_state=False) as ctl:
        root_item = ctl._root_item
        root = controller.Root(root_item)
        window_item = root_item.children[0]
        view = window_item.view
        state = web.summon(default_layout.state.window_list[0])
        await window_commands.duplicate_window(root, view, state)
        assert len(root_item.children) == 2
        await feed.wait_for_diffs(count=1)

        # Canned ctl item.
        item_piece = window_item.hook.canned_item_piece
        ctl_ctx = ctx.clone_with(controller=ctl)
        item = canned_ctl_item_factory(item_piece, ctl_ctx)
        assert item.hook.canned_item_piece == item_piece
