from unittest.mock import Mock

from . import htypes
from .code.context import Context
from .services import (
    mosaic,
    web,
    )
from .fixtures import qapp_fixtures
from .tested.code import tab_groups


def test_move_tab_to_new_group(qapp, view_reg):
    label = htypes.label.view("Sample label")
    inner_tabs_piece = htypes.auto_tabs.view(
        tabs=(
            mosaic.put(label),
            mosaic.put(label),
            ),
        )
    outer_tabs_piece = htypes.tabs.view(
        tabs=(
            htypes.tabs.tab("Outer", mosaic.put(inner_tabs_piece)),
            ),
        )
    label_state = htypes.label.state()
    inner_tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=(
            mosaic.put(label_state),
            mosaic.put(label_state),
            ),
        )
    outer_tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(inner_tabs_state),),
        )
    ctx = Context()
    view = view_reg.animate(outer_tabs_piece, ctx)
    view.set_controller_hook(Mock())
    view.tabs[0].view.set_controller_hook(Mock())
    widget = view.construct_widget(outer_tabs_state, ctx)
    tab_groups.move_tab_to_new_group(view, widget, outer_tabs_state, ctx)
    assert len(view.piece.tabs) == 2
    new_inner_piece = web.summon(view.piece.tabs[0].ctl)
    assert len(new_inner_piece.tabs) == 1
