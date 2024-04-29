import logging

from . import htypes
from .services import (
    mark,
    view_creg,
    web,
    )
from .code.list_diff import ListDiff
from .code.view import Diff
from .code.tabs import TabsView

log = logging.getLogger(__name__)


def tab_piece_label(piece):
    if isinstance(piece, htypes.box_layout.view):
        piece = web.summon(piece.elements[0].view)
    if isinstance(piece, htypes.navigator.view):
        piece = web.summon(piece.current_model)
    return str(piece)[:40]


def tab_piece_ref_label(piece_ref):
    piece = web.summon(piece_ref)
    return tab_piece_label(piece)


class AutoTabsView(TabsView):

    @classmethod
    def from_piece(cls, piece, ctx):
        tabs = [
            cls._Tab(
                view=view_creg.invite(view_ref, ctx),
                label=tab_piece_ref_label(view_ref),
                )
            for view_ref in piece.tabs
            ]
        return cls(tabs)

    @property
    def piece(self):
        tabs = tuple(tab.ctl for tab in super().piece.tabs)
        return htypes.auto_tabs.view(tabs)

    def model_changed(self, widget, model):
        idx = super().get_current(widget)
        item = super().items()[idx]
        text = tab_piece_label(item.view.piece)
        super().set_tab_text(widget, idx, text)

    def insert_tab(self, ctx, widget, idx, tab_view, tab_state):
        label = tab_piece_label(tab_view.piece)
        super().insert_tab(ctx, widget, idx, label, tab_view, tab_state)


@mark.ui_command(htypes.auto_tabs.view)
def duplicate_tab(ctx, view, widget, state):
    log.info("Duplicate tab: %s / %s", view, state)
    current_view = view.current_tab(widget).view
    current_widget = view.current_widget(widget)
    tab_state = current_view.widget_state(current_widget)
    new_view = view_creg.animate(current_view.piece, ctx)
    view.insert_tab(ctx, widget, state.current_tab + 1, new_view, tab_state)


@mark.ui_command(htypes.auto_tabs.view)
def close_tab(view, widget, state):
    log.info("Close tab: %s / %s", view, state)
    if view.tab_count == 1:
        log.info("Close tab: won't close last tab")
        return
    view.close_tab(widget, state.current_tab)
