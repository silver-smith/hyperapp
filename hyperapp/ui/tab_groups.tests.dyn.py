from unittest.mock import Mock

from PySide6 import QtWidgets

from . import htypes
from .code.context import Context
from .services import (
    mosaic,
    view_creg,
    web,
    )
from .tested.code import tab_groups


def test_move_tab_to_new_group():
    adapter_piece = htypes.str_adapter.static_str_adapter("Sample text")
    text_piece = htypes.text.readonly_view(mosaic.put(adapter_piece))
    inner_tabs_piece = htypes.auto_tabs.view(
        tabs=(
            mosaic.put(text_piece),
            mosaic.put(text_piece),
            ),
        )
    outer_tabs_piece = htypes.tabs.view(
        tabs=(
            htypes.tabs.tab("Outer", mosaic.put(inner_tabs_piece)),
            ),
        )
    text_state = htypes.text.state()
    inner_tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=(
            mosaic.put(text_state),
            mosaic.put(text_state),
            ),
        )
    outer_tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(inner_tabs_state),),
        )
    ctx = Context()
    app = QtWidgets.QApplication()
    try:
        view = view_creg.animate(outer_tabs_piece, ctx)
        view.set_controller_hook(Mock())
        view.tabs[0].view.set_controller_hook(Mock())
        widget = view.construct_widget(outer_tabs_state, ctx)
        tab_groups.move_tab_to_new_group(view, widget, outer_tabs_state, ctx)
        assert len(view.piece.tabs) == 2
        new_inner_piece = web.summon(view.piece.tabs[0].ctl)
        assert len(new_inner_piece.tabs) == 1
    finally:
        app.shutdown()
