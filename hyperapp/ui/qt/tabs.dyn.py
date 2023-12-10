import logging

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mark,
    mosaic,
    ui_command_factory,
    ui_ctl_creg,
    web,
    )
from .code.list_diff import ListDiff, ListDiffInsert

log = logging.getLogger(__name__)


class TabsCtl:

    @classmethod
    def from_piece(cls, layout):
        tabs = [
            (tab.label, ui_ctl_creg.invite(tab.ctl))
            for tab in layout.tabs
            ]
        ctl = cls(layout, tabs)
        commands = ui_command_factory(layout, ctl)
        ctl._commands = commands
        return ctl

    def __init__(self, layout, tabs):
        self._layout = layout
        self._tabs = tabs  # (label, ctl) list
        self._commands = None

    def construct_widget(self, state, ctx):
        tabs = QtWidgets.QTabWidget()
        for idx, (label, ctl) in enumerate(self._tabs):
            tab_state = web.summon(state.tabs[idx])
            w = ctl.construct_widget(tab_state, ctx)
            tabs.addTab(w, label)
        return tabs

    def widget_state(self, widget):
        return htypes.tabs.state(
            current_tab=widget.currentIndex(),
            tabs=[
                mosaic.put(ctl.widget_state(widget.widget(idx)))
                for idx, (label, ctl) in enumerate(self._tabs)
                ],
        )

    def bind_commands(self, layout, widget, wrapper):
        return [command.bind(layout, widget, wrapper) for command in self._commands]

    def apply(self, widget, layout_diff, state_diff):
        log.info("Tabs: apply: %s / %s", layout_diff, state_diff)
        if isinstance(layout_diff, ListDiffInsert):
            tab_ctl = ui_ctl_creg.invite(layout_diff.item.ctl)
            tab_state = web.summon(state_diff.item)
            w = tab_ctl.construct_widget(tab_state, ctx=None)
            widget.insertTab(layout_diff.idx, w, layout_diff.item.label)
            self._tabs.insert(layout_diff.idx, (layout_diff.item.label, tab_ctl))
            self._layout = htypes.tabs.layout(layout_diff.apply(self._layout.tabs))
            return self._layout
        else:
            raise NotImplementedError(f"Not implemented: tab.apply({layout_diff})")


@mark.ui_command(htypes.tabs.layout)
def duplicate(layout, state):
    log.info("Duplicate tab: %s / %s", layout, state)
    layout_diff = ListDiff.insert(
        idx=state.current_tab,
        item=layout.tabs[state.current_tab],
        )
    state_diff = ListDiff.insert(
        idx=state.current_tab,
        item=state.tabs[state.current_tab],
        )
    return (layout_diff, state_diff)
