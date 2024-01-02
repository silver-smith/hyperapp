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
        tabs = [
            (tab.label, ui_ctl_creg.invite(tab.ctl))
            for tab in layout.tabs
            ]
        return cls(layout, tabs)

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
        tabs.setCurrentIndex(state.current_tab)
        tabs.currentChanged.connect(partial(self._on_current_changed, ctx.command_hub, tabs))
        return tabs

    def widget_state(self, widget):
        return htypes.tabs.state(
            current_tab=widget.currentIndex(),
            tabs=[
                mosaic.put(ctl.widget_state(widget.widget(idx)))
                for idx, (label, ctl) in enumerate(self._tabs)
                ],
        )

    def get_commands(self, layout, widget, wrapper):
        if self._commands is None:
            self._commands = ui_command_factory(layout, self)
        idx = widget.currentIndex()
        _, tab_ctl = self._tabs[idx]
        tab_layout = web.summon(layout.tabs[idx].ctl)
        tab_commands = tab_ctl.get_commands(
            tab_layout, widget.widget(idx), partial(self._wrapper, wrapper, idx))
        my_commands = [command.bind(layout, widget, wrapper) for command in self._commands]
        return [*my_commands, *tab_commands]

    def _wrapper(self, wrapper, idx, diffs):
        layout_diff, state_diff = diffs
        return wrapper((
            ListDiffModify(idx, layout_diff),
            ListDiffModify(idx, state_diff),
            ))

    def apply(self, ctx, layout, widget, layout_diff, state_diff):
        log.info("Tabs: apply: %s -> %s / %s", layout, layout_diff, state_diff)
        if isinstance(layout_diff, ListDiffInsert):
            idx = layout_diff.idx
            old_state = self.widget_state(widget)
            tab_ctl = ui_ctl_creg.invite(layout_diff.item.ctl)
            tab_state = web.summon(state_diff.item)
            w = tab_ctl.construct_widget(tab_state, ctx)
            widget.insertTab(idx + 1, w, layout_diff.item.label)
            widget.setCurrentIndex(idx + 1)
            self._tabs.insert(idx, (layout_diff.item.label, tab_ctl))
            new_layout = htypes.tabs.layout(layout_diff.apply(self._layout.tabs))
            new_state_tabs = layout_diff.insert(old_state.tabs, mosaic.put(tab_state))
            new_state = htypes.tabs.state(
                current_tab=idx + 1,
                tabs=new_state_tabs,
                )
            self._layout = new_layout
            return (new_layout, new_state)
        if isinstance(layout_diff, ListDiffModify):
            idx = layout_diff.idx
            label, old_tab_ctl = self._tabs[idx]
            old_tab_layout = web.summon(layout.tabs[idx].ctl)
            new_tab_layout, new_tab_state = old_tab_ctl.apply(
                ctx, old_tab_layout, widget.widget(idx), layout_diff.item_diff, state_diff.item_diff)
            new_tab_ctl = ui_ctl_creg.animate(new_tab_layout)
            w = new_tab_ctl.construct_widget(new_tab_state, ctx)
            widget.removeTab(idx)
            widget.insertTab(idx, w, label)
            widget.setCurrentIndex(idx)
            self._tabs = layout_diff.replace(self._tabs, (label, new_tab_ctl))
            new_layout_tabs = layout_diff.replace(
                self._layout.tabs,
                htypes.tabs.tab(label, mosaic.put(new_tab_layout)),
                )
            new_layout = htypes.tabs.layout(new_layout_tabs)
            self._layout = new_layout
            return (new_layout, self.widget_state(widget))
        else:
            raise NotImplementedError(f"Not implemented: tab.apply({layout_diff})")

    def _on_current_changed(self, command_hub, widget, index):
        log.info("Tabs: current changed for %s to %s", widget, index)


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
