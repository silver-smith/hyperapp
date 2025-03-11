import logging

from . import htypes
from .services import (
    web,
    )
from .code.mark import mark
from .code.list_diff import ListDiff
from .code.tabs import TabsView

log = logging.getLogger(__name__)


def tab_piece_label(piece):
    return str(piece)[:40]


def tab_piece_ref_label(piece_ref):
    piece = web.summon(piece_ref)
    return tab_piece_label(piece)


class AutoTabsView(TabsView):

    @classmethod
    @mark.view
    def from_piece(cls, piece, ctx, view_reg):
        tabs = cls._data_to_tabs(piece.tabs, ctx, view_reg)
        return cls(tabs)

    @property
    def piece(self):
        return htypes.auto_tabs.view(self._tabs_data)

    async def children_changed(self, ctx, rctx, widget):
        try:
            model = rctx.current_model
        except KeyError:
            text = "Unknown"
        else:
            text = tab_piece_label(model)
        idx = super().get_current(widget)
        super().set_tab_text(widget, idx, text)

    def insert_tab(self, ctx, widget, idx, tab_view, tab_state):
        label = tab_piece_label(tab_view.piece)
        super().insert_tab(ctx, widget, idx, label, tab_view, tab_state)


@mark.ui_command(htypes.auto_tabs.view)
def duplicate_tab(ctx, view, widget, state, view_reg):
    log.info("Duplicate tab: %s / %s", view, state)
    current_view = view.current_tab(widget).view
    current_widget = view.current_widget(widget)
    tab_state = current_view.widget_state(current_widget)
    new_view = view_reg.animate(current_view.piece, ctx)
    view.insert_tab(ctx, widget, state.current_tab + 1, new_view, tab_state)


@mark.ui_command(htypes.auto_tabs.view)
def close_tab(view, widget, state):
    log.info("Close tab: %s / %s", view, state)
    if view.tab_count == 1:
        log.info("Close tab: won't close last tab")
        return
    view.close_tab(widget, state.current_tab)
