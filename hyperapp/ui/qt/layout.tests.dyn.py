from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .code.ui_command import UnboundUiCommand
from .fixtures import qapp_fixtures, feed_fixtures
from .tested.code import controller
from .tested.code import layout


def make_text_layout():
    adapter = htypes.str_adapter.static_str_adapter()
    return htypes.text.readonly_view(mosaic.put(adapter))


def make_default_piece():
    text = make_text_layout()
    navigator = htypes.navigator.view(
        current_view=mosaic.put(text),
        current_model=mosaic.put("Sample model"),
        prev=None,
        next=None,
        )
    tabs_piece = htypes.auto_tabs.view(
        tabs=(mosaic.put(navigator),),
        )
    window_piece = htypes.window.view(
        menu_bar_ref=mosaic.put(htypes.menu_bar.view()),
        central_view_ref=mosaic.put(tabs_piece),
        )
    return htypes.root.view((
        mosaic.put(window_piece),
        ))


def make_default_state():
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
def default_layout():
    return htypes.root.layout(
        piece=make_default_piece(),
        state=make_default_state(),
        )


class PhonyLayoutBundle:

    def load_piece(self):
        raise FileNotFoundError("Phony layout bundle")

    def save_piece(self, piece):
        pass


def _sample_auto_tabs_command():
    pass


@mark.config_fixture('view_ui_command_reg')
def view_ui_command_reg_config(partial_ref):
    system_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=(),
        service_params=(),
        raw_fn=_sample_auto_tabs_command,
        bound_fn=_sample_auto_tabs_command,
        )
    command = UnboundUiCommand(
        d=htypes.layout_tests.sample_command_d(),
        ctx_fn=system_fn,
        properties=htypes.command.properties(False, False, False),
        groups=set(),
        )
    return {htypes.auto_tabs.view: [command]}


@mark.fixture
def lcs():
    lcs = Mock()
    lcs.get.return_value = None  # command list - mock is not iterable.
    return lcs


@mark.fixture
def ctx(lcs):
    return Context(lcs=lcs)


@mark.fixture.obj
async def ctl(controller_running, default_layout, ctx):
    async with controller_running(PhonyLayoutBundle(), default_layout, ctx, show=False, load_state=False) as ctl:
        yield ctl


async def test_layout_tree(qapp, ctl):
    piece = htypes.layout.view()
    items = layout.layout_tree(piece, None, ctl)
    assert items
    parent = htypes.layout.item(1, "Some item", True, "Item description")
    layout.layout_tree(piece, parent, ctl)


async def test_enum_layout_tree_commands(qapp, ctl):
    piece = htypes.layout.view()
    windows = layout.layout_tree(piece, None, ctl)
    window_items = layout.layout_tree(piece, windows[0], ctl)
    commands = layout.enum_layout_tree_commands(piece, window_items[1], ctl)
    assert commands


async def test_open_view_item_commands():
    piece = htypes.layout.view()
    item = Mock()
    item.id = 123
    result = await layout.open_view_item_commands(piece, current_item=item)
    assert result


async def test_view_item_commands(qapp, lcs, ctx, ctl):
    ctx = ctx.clone_with(controller=ctl)
    layout_piece = htypes.layout.view()
    windows = layout.layout_tree(layout_piece, None, ctl)
    window_items = layout.layout_tree(layout_piece, windows[0], ctl)
    item_id = window_items[1].id
    command_list_piece = htypes.layout.command_list(item_id)
    commands = layout.view_item_commands(command_list_piece, ctl, lcs, ctx)
    assert commands


def mock_run_input_key_dialog():
    return ''


def test_set_shortcut(data_to_ref, lcs):
    piece = htypes.layout.command_list(item_id=0)
    current_item = htypes.layout.command_item(
        name="<unused>",
        shortcut="",
        groups="<unused>",
        wrapped_groups="<unused>",
        command_d=data_to_ref(htypes.layout_tests.sample_command_d()),
        )
    layout.run_key_input_dialog = mock_run_input_key_dialog
    layout.set_shortcut(piece, current_item, lcs)
    lcs.set.assert_called_once()


async def test_add_view_command():
    piece = htypes.layout.command_list(item_id=123)
    result = await layout.add_view_command(piece, current_item=None)


async def test_open_layout_tree():
    result = await layout.open_layout_tree()
