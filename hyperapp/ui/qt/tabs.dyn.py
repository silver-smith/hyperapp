import logging
from collections import namedtuple
from functools import partial

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.view import Item, View

log = logging.getLogger(__name__)


class TabsView(View):

    _Tab = namedtuple('_Tab', 'view label')

    @classmethod
    @mark.view
    def from_piece(cls, piece, ctx, view_reg):
        tabs = [
            cls._Tab(view_reg.invite(rec.ctl, ctx), rec.label)
            for rec in piece.tabs
            ]
        return cls(tabs)

    def __init__(self, tabs):
        super().__init__()
        self._tabs = tabs  # list[_Tab]
        self._current_changed_hook_enabled = True

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
        tabs.currentChanged.connect(self._call_current_changed_hook)
        return tabs

    def _call_current_changed_hook(self):
        if self._current_changed_hook_enabled:
            self._ctl_hook.current_changed()

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

    def current_tab(self, widget):
        idx = widget.currentIndex()
        return self._tabs[idx]

    def current_widget(self, widget):
        idx = widget.currentIndex()
        return widget.widget(idx)

    @property
    def tab_count(self):
        return len(self._tabs)

    @property
    def tabs(self):
        return self._tabs

    def insert_tab(self, ctx, widget, idx, label, tab_view, tab_state):
        w = tab_view.construct_widget(tab_state, ctx)
        new_tab = self._Tab(tab_view, label)
        self._tabs.insert(idx, new_tab)
        widget.insertTab(idx, w, label)
        self._current_changed_hook_enabled = False
        try:
            widget.setCurrentIndex(idx)
        finally:
            self._current_changed_hook_enabled = True
        self._ctl_hook.element_inserted(idx)

    def close_tab(self, widget, idx):
        self._current_changed_hook_enabled = False
        try:
            widget.removeTab(idx)
            del self._tabs[idx]
            widget.setCurrentIndex(idx)
        finally:
            self._current_changed_hook_enabled = True
        self._ctl_hook.element_removed(idx)

    def items(self):
        return [
            Item(tab.label, tab.view)
            for idx, tab in enumerate(self._tabs)
            ]

    def item_widget(self, widget, idx):
        return widget.widget(idx)

    def set_tab_text(self, widget, idx, text):
        widget.setTabText(idx, text)


@mark.ui_model_command(htypes.tabs.view)
def open_tab_list(view):
    log.info("Open tab list: %s", view)
    return [
        htypes.tabs.list_item(item.name)
        for item in view.items()
        ]
