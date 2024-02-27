import logging
from collections import namedtuple
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
from .code.list_diff import ListDiff
from .code.view import Item, View

log = logging.getLogger(__name__)


class TabsView(View):

    _Tab = namedtuple('_Tab', 'view label')

    @classmethod
    def from_piece(cls, piece):
        tabs = [
            cls._Tab(ui_ctl_creg.invite(rec.ctl), rec.label)
            for rec in piece.tabs
            ]
        return cls(tabs)

    def __init__(self, tabs):
        super().__init__()
        self._tabs = tabs  # list[_Tab]
        self._on_child_changed = lambda idx, w: None

    @property
    def piece(self):
        tabs = [
            htypes.tabs.tab(
                label=tab.label,
                ctl=mosaic.put(tab.view.piece),
                )
            for tab in self._tabs
            ]
        return htypes.tabs.layout(tabs)

    def construct_widget(self, state, ctx):
        tabs = QtWidgets.QTabWidget()
        for tab, tab_state_ref in zip(self._tabs, state.tabs):
            tab_state = web.summon(tab_state_ref)
            w = tab.view.construct_widget(tab_state, ctx)
            tabs.addTab(w, tab.label)
        tabs.setCurrentIndex(state.current_tab)
        tabs.currentChanged.connect(partial(self._on_current_changed, ctx.command_hub))
        return tabs

    def get_current(self, widget):
        return widget.currentIndex()

    def set_on_child_changed(self, on_changed):
        self._on_child_changed = on_changed

    def set_on_current_changed(self, widget, on_changed):
        widget.currentChanged.disconnect()
        widget.currentChanged.connect(lambda idx: on_changed())

    def wrapper(self, widget, diffs):
        layout_diff, state_diff = diffs
        idx = widget.currentIndex()
        return (
            ListDiff.Modify(idx, layout_diff),
            ListDiff.Modify(idx, state_diff),
            )

    def widget_state(self, widget):
        tabs = []
        for idx, tab in enumerate(self._tabs):
            tab_state = tab.view.widget_state(widget.widget(idx))
            tabs.append(mosaic.put(tab_state))
        return htypes.tabs.state(
            current_tab=widget.currentIndex(),
            tabs=tabs,
            )

    def apply(self, ctx, widget, layout_diff, state_diff):
        log.info("Tabs: apply: %s / %s", layout_diff, state_diff)
        if isinstance(layout_diff, ListDiff.Insert):
            idx = layout_diff.idx
            old_state = self.widget_state(widget)
            tab_piece = web.summon(layout_diff.item.ctl)
            tab_view = ui_ctl_creg.animate(tab_piece)
            tab_state = web.summon(state_diff.item)
            w = tab_view.construct_widget(tab_state, ctx)
            new_tab = self._Tab(tab_view, layout_diff.item.label)
            self._tabs = layout_diff.insert(self._tabs, new_tab)
            widget.insertTab(idx, w, layout_diff.item.label)
            widget.setCurrentIndex(idx)
            return (self.widget_state(widget), False)
        if isinstance(layout_diff, ListDiff.Modify):
            idx = layout_diff.idx
            tab = self._tabs[idx]
            result = tab.view.apply(
                ctx, widget.widget(idx), layout_diff.item_diff, state_diff.item_diff)
            if result is None:
                return None
            new_tab_state, replace = result
            if replace:
                w = tab.view.construct_widget(new_tab_state, ctx)
                widget.removeTab(idx)
                widget.insertTab(idx, w, tab.label)
                widget.setCurrentIndex(idx)
                self._on_child_changed(idx, w)
            return (self.widget_state(widget), False)
        if isinstance(layout_diff, ListDiff.Remove):
            idx = layout_diff.idx
            widget.removeTab(idx)
            widget.setCurrentIndex(idx)
            self._tabs = layout_diff.remove(self._tabs)
            return (self.widget_state(widget), False)
        else:
            raise NotImplementedError(f"Not implemented: tab.apply({layout_diff})")

    def items(self, widget):
        return [
            Item(tab.label, tab.view, widget.widget(idx))
            for idx, tab in enumerate(self._tabs)
            ]

    def _on_current_changed(self, command_hub, widget, index):
        log.info("Tabs: current changed for %s to %s", widget, index)


@mark.ui_command(htypes.tabs.layout)
def duplicate(layout, state):
    log.info("Duplicate tab: %s / %s", layout, state)
    layout_diff = ListDiff.Insert(
        idx=state.current_tab + 1,
        item=layout.tabs[state.current_tab],
        )
    state_diff = ListDiff.Insert(
        idx=state.current_tab + 1,
        item=state.tabs[state.current_tab],
        )
    return (layout_diff, state_diff)


@mark.ui_command(htypes.tabs.layout)
def close_tab(layout, state):
    log.info("Close tab: %s / %s", layout, state)
    if len(layout.tabs) == 1:
        log.info("Close tab: won't close last tab")
        return None
    layout_diff = ListDiff.Remove(
        idx=state.current_tab,
        )
    state_diff = ListDiff.Remove(
        idx=state.current_tab,
        )
    return (layout_diff, state_diff)
