import logging
from functools import partial

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mark,
    mosaic,
    ui_command_factory,
    ui_ctl_creg,
    web,
    )
from .code.list_diff import ListDiff, ListDiffInsert, ListDiffModify

log = logging.getLogger(__name__)


class TabsCtl:

    @classmethod
    def from_piece(cls, layout):
        return cls()

    def construct_widget(self, piece, state, ctx):
        tabs = QtWidgets.QTabWidget()
        for idx, tab in enumerate(piece.tabs):
            tab_piece = web.summon(tab.ctl)
            tab_view = ui_ctl_creg.animate(tab_piece)
            tab_state = web.summon(state.tabs[idx])
            w = tab_view.construct_widget(tab_piece, tab_state, ctx)
            tabs.addTab(w, tab.label)
        tabs.setCurrentIndex(state.current_tab)
        tabs.currentChanged.connect(partial(self._on_current_changed, ctx.command_hub, tabs))
        return tabs

    def get_current(self, piece, widget):
        idx = widget.currentIndex()
        return (piece.tabs[idx].ctl, widget.widget(idx))

    def wrapper(self, widget, diffs):
        layout_diff, state_diff = diffs
        idx = widget.currentIndex()
        return (
            ListDiffModify(idx, layout_diff),
            ListDiffModify(idx, state_diff),
            )

    def widget_state(self, piece, widget):
        tabs = []
        for idx, tab in enumerate(piece.tabs):
            tab_piece = web.summon(tab.ctl)
            tab_view = ui_ctl_creg.animate(tab_piece)
            tab_state = tab_view.widget_state(tab_piece, widget.widget(idx))
            tabs.append(mosaic.put(tab_state))
        return htypes.tabs.state(
            current_tab=widget.currentIndex(),
            tabs=tabs,
            )

    def apply(self, ctx, piece, widget, layout_diff, state_diff):
        log.info("Tabs: apply: %s -> %s / %s", piece, layout_diff, state_diff)
        if isinstance(layout_diff, ListDiffInsert):
            idx = layout_diff.idx
            old_state = self.widget_state(piece, widget)
            tab_piece = web.summon(layout_diff.item.ctl)
            tab_view = ui_ctl_creg.animate(tab_piece)
            tab_state = web.summon(state_diff.item)
            w = tab_view.construct_widget(tab_piece, tab_state, ctx)
            widget.insertTab(idx, w, layout_diff.item.label)
            widget.setCurrentIndex(idx)
            new_piece = htypes.tabs.layout(layout_diff.apply(piece.tabs))
            return (new_piece, self.widget_state(new_piece, widget))
        if isinstance(layout_diff, ListDiffModify):
            idx = layout_diff.idx
            old_tab_piece = web.summon(piece.tabs[idx].ctl)
            old_tab_view = ui_ctl_creg.animate(old_tab_piece)
            label = piece.tabs[idx].label
            new_tab_piece, new_tab_state = old_tab_view.apply(
                ctx, old_tab_piece, widget.widget(idx), layout_diff.item_diff, state_diff.item_diff)
            new_tab_view = ui_ctl_creg.animate(new_tab_piece)
            w = new_tab_view.construct_widget(new_tab_piece, new_tab_state, ctx)
            widget.removeTab(idx)
            widget.insertTab(idx, w, label)
            widget.setCurrentIndex(idx)
            new_tabs = layout_diff.replace(
                piece.tabs,
                htypes.tabs.tab(label, mosaic.put(new_tab_piece)),
                )
            new_piece = htypes.tabs.layout(new_tabs)
            return (new_piece, self.widget_state(new_piece, widget))
        else:
            raise NotImplementedError(f"Not implemented: tab.apply({layout_diff})")

    def _on_current_changed(self, command_hub, widget, index):
        log.info("Tabs: current changed for %s to %s", widget, index)


@mark.ui_command(htypes.tabs.layout)
def duplicate(layout, state):
    log.info("Duplicate tab: %s / %s", layout, state)
    layout_diff = ListDiff.insert(
        idx=state.current_tab + 1,
        item=layout.tabs[state.current_tab],
        )
    state_diff = ListDiff.insert(
        idx=state.current_tab + 1,
        item=state.tabs[state.current_tab],
        )
    return (layout_diff, state_diff)
