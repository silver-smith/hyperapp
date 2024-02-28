import logging

from . import htypes
from .services import (
    mark,
    ui_ctl_creg,
    web,
    )
from .code.list_diff import ListDiff
from .code.wrapper_view import WrapperView

log = logging.getLogger(__name__)


def tab_label(piece_ref):
    piece = web.summon(piece_ref)
    if isinstance(piece, htypes.navigator.layout):
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
        base_piece = htypes.tabs.layout(tabs)
        base = ui_ctl_creg.animate(base_piece)
        return cls(base)

    @property
    def piece(self):
        tabs = [tab.ctl for tab in self._base.piece.tabs]
        return htypes.auto_tabs.view(tabs)

    def apply(self, ctx, widget, layout_diff, state_diff):
        log.info("AutoTabs: apply: %s / %s", layout_diff, state_diff)
        if isinstance(layout_diff, ListDiff.Insert):
            base_layout_diff = ListDiff.Insert(
                idx=layout_diff.idx,
                item=htypes.tabs.tab(
                    label=tab_label(layout_diff.item),
                    ctl=layout_diff.item,
                    ),
                )
            return self._base.apply(ctx, widget, base_layout_diff, state_diff)
        elif isinstance(layout_diff, ListDiff.Modify):
            result = self._base.apply(ctx, widget, layout_diff, state_diff)
            label = tab_label(self.piece.tabs[layout_diff.idx])
            widget.setTabText(layout_diff.idx, label)
            return result
        elif isinstance(layout_diff, ListDiff.Remove):
            return self._base.apply(ctx, widget, layout_diff, state_diff)
        else:
            raise NotImplementedError(f"Not implemented: auto_tab.apply({layout_diff})")


@mark.ui_command(htypes.auto_tabs.view)
def duplicate_tab(piece, state):
    log.info("Duplicate tab: %s / %s", piece, state)
    layout_diff = ListDiff.Insert(
        idx=state.current_tab + 1,
        item=piece.tabs[state.current_tab],
        )
    state_diff = ListDiff.Insert(
        idx=state.current_tab + 1,
        item=state.tabs[state.current_tab],
        )
    return (layout_diff, state_diff)


@mark.ui_command(htypes.auto_tabs.view)
def close_tab(piece, state):
    log.info("Close tab: %s / %s", piece, state)
    if len(piece.tabs) == 1:
        log.info("Close tab: won't close last tab")
        return None
    layout_diff = ListDiff.Remove(
        idx=state.current_tab,
        )
    state_diff = ListDiff.Remove(
        idx=state.current_tab,
        )
    return (layout_diff, state_diff)
