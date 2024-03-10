import logging

from . import htypes
from .services import (
    mark,
    ui_ctl_creg,
    web,
    )
from .code.list_diff import ListDiff
from .code.view import Diff
from .code.wrapper_view import WrapperView

log = logging.getLogger(__name__)


def tab_label(piece_ref):
    piece = web.summon(piece_ref)
    if isinstance(piece, htypes.box_layout.view):
        piece = web.summon(piece.elements[0].view)
    if isinstance(piece, htypes.navigator.view):
        piece = web.summon(piece.current_model)
    return str(piece)[:40]


class AutoTabsView(WrapperView):

    @classmethod
    def from_piece(cls, piece):
        tabs = [
            htypes.tabs.tab(
                label=tab_label(view_ref),
                ctl=view_ref,
                )
            for idx, view_ref in enumerate(piece.tabs)
            ]
        base_piece = htypes.tabs.view(tabs)
        base = ui_ctl_creg.animate(base_piece)
        return cls(base)

    @property
    def piece(self):
        tabs = [tab.ctl for tab in self._base.piece.tabs]
        return htypes.auto_tabs.view(tabs)

    def apply(self, ctx, widget, diff):
        log.info("AutoTabs: apply: %s", diff)
        if isinstance(diff.piece, ListDiff.Insert):
            base_diff_piece = ListDiff.Insert(
                idx=diff.piece.idx,
                item=htypes.tabs.tab(
                    label=tab_label(diff.piece.item),
                    ctl=diff.piece.item,
                    ),
                )
            base_diff = Diff(base_diff_piece, diff.state)
            return self._base.apply(ctx, widget, base_diff)
        elif isinstance(diff.piece, ListDiff.Remove):
            return self._base.apply(ctx, widget, diff)
        else:
            raise NotImplementedError(f"Not implemented: auto_tab.apply({diff.piece})")


@mark.ui_command(htypes.auto_tabs.view)
def duplicate_tab(piece, state):
    log.info("Duplicate tab: %s / %s", piece, state)
    return Diff(
        piece=ListDiff.Insert(
            idx=state.current_tab + 1,
            item=piece.tabs[state.current_tab],
            ),
        state=ListDiff.Insert(
            idx=state.current_tab + 1,
            item=state.tabs[state.current_tab],
            ),
        )


@mark.ui_command(htypes.auto_tabs.view)
def close_tab(piece, state):
    log.info("Close tab: %s / %s", piece, state)
    if len(piece.tabs) == 1:
        log.info("Close tab: won't close last tab")
        return None
    return Diff(
        piece=ListDiff.Remove(
            idx=state.current_tab,
            ),
        state=ListDiff.Remove(
            idx=state.current_tab,
            ),
        )
