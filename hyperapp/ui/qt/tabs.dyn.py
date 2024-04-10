import logging
from collections import namedtuple
from functools import partial

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mark,
    mosaic,
    view_creg,
    web,
    )
from .code.list_diff import ListDiff
from .code.view import Diff, Item, View

log = logging.getLogger(__name__)


class TabsView(View):

    _Tab = namedtuple('_Tab', 'view label')

    @classmethod
    def from_piece(cls, piece):
        tabs = [
            cls._Tab(view_creg.invite(rec.ctl), rec.label)
            for rec in piece.tabs
            ]
        return cls(tabs)

    def __init__(self, tabs):
        super().__init__()
        self._tabs = tabs  # list[_Tab]

    @property
    def piece(self):
        tabs = tuple(
            htypes.tabs.tab(
                label=tab.label,
                ctl=mosaic.put(tab.view.piece),
                )
            for tab in self._tabs
            )
        return htypes.tabs.view(tabs)

    def construct_widget(self, state, ctx):
        tabs = QtWidgets.QTabWidget()
        for tab, tab_state_ref in zip(self._tabs, state.tabs):
            tab_state = web.summon(tab_state_ref)
            w = tab.view.construct_widget(tab_state, ctx)
            tabs.addTab(w, tab.label)
        tabs.setCurrentIndex(state.current_tab)
        tabs.currentChanged.connect(lambda idx: self._ctl_hook.current_changed())
        return tabs

    def replace_child_widget(self, widget, idx, new_child_widget):
        tab = self._tabs[idx]
        widget.removeTab(idx)
        widget.insertTab(idx, new_child_widget, tab.label)
        widget.setCurrentIndex(idx)

    def get_current(self, widget):
        return widget.currentIndex()

    def widget_state(self, widget):
        tabs = []
        for idx, tab in enumerate(self._tabs):
            tab_state = tab.view.widget_state(widget.widget(idx))
            tabs.append(mosaic.put(tab_state))
        return htypes.tabs.state(
            current_tab=widget.currentIndex(),
            tabs=tuple(tabs),
            )

    def apply(self, ctx, widget, diff):
        log.info("Tabs: apply: %s", diff)
        if isinstance(diff.piece, ListDiff.Insert):
            idx = diff.piece.idx
            old_state = self.widget_state(widget)
            tab_piece = web.summon(diff.piece.item.ctl)
            tab_view = view_creg.animate(tab_piece)
            tab_state = web.summon(diff.state.item)
            w = tab_view.construct_widget(tab_state, ctx)
            new_tab = self._Tab(tab_view, diff.piece.item.label)
            self._tabs = diff.piece.insert(self._tabs, new_tab)
            widget.insertTab(idx, w, diff.piece.item.label)
            widget.setCurrentIndex(idx)
            self._ctl_hook.element_inserted(idx)
        elif isinstance(diff.piece, ListDiff.Remove):
            idx = diff.piece.idx
            widget.removeTab(idx)
            widget.setCurrentIndex(idx)
            self._tabs = diff.piece.remove(self._tabs)
            self._ctl_hook.item_element_removed(idx)
        else:
            raise NotImplementedError(f"Not implemented: tab.apply({diff.piece})")

    def items(self):
        return [
            Item(tab.label, tab.view)
            for idx, tab in enumerate(self._tabs)
            ]

    def item_widget(self, widget, idx):
        return widget.widget(idx)
