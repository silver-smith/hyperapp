from unittest.mock import Mock

from . import htypes
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import menu_bar


def make_piece():
    return htypes.menu_bar.view()


def make_state():
    return htypes.menu_bar.state()


async def test_widget(qapp):
    ctx = Context(
        lcs=Mock(),
        )
    piece = make_piece()
    state = make_state()
    command = Mock(
        d=htypes.menu_bar_tests.sample_command_d(),
        groups={htypes.command_groups.global_d()},
        enabled=True,
        )

    view = menu_bar.MenuBarView.from_piece(piece, ctx)
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert state
    rctx = Context(commands=[command])
    await view.children_changed(ctx, rctx, widget, save_layout=False)
