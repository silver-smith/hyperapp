from PySide6 import QtWidgets

from . import htypes
from .tested.code import tabs
from .services import (
    mosaic,
    web,
    )
from .code.context import Context
from .code.command_hub import CommandHub


def make_inner_layout():
    adapter_layout = htypes.str_adapter.static_str_adapter("Sample text")
    tab_layout = htypes.text.view_layout(mosaic.put(adapter_layout))
    return htypes.tabs.layout(
        tabs=[
            htypes.tabs.tab("One", mosaic.put(tab_layout))],
        )


def make_outer_layout(tab_layout):
    return htypes.tabs.layout(
        tabs=[
            htypes.tabs.tab("Inner", mosaic.put(tab_layout))],
        )


def make_inner_state():
    tab_state = htypes.text.state()
    return htypes.tabs.state(
        current_tab=0,
        tabs=[mosaic.put(tab_state)],
        )


def make_outer_state(tab_state):
    return htypes.tabs.state(
        current_tab=0,
        tabs=[mosaic.put(tab_state)],
        )


def test_tabs():
    ctx = Context(command_hub=CommandHub())
    layout = make_inner_layout()
    state = make_inner_state()
    app = QtWidgets.QApplication()
    try:
        ctl = tabs.TabsCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx)
        state = ctl.widget_state(widget)
        assert state
    finally:
        app.shutdown()


def test_duplicate():
    ctx = Context(command_hub=CommandHub())
    layout = make_inner_layout()
    state = make_inner_state()
    app = QtWidgets.QApplication()
    try:
        ctl = tabs.TabsCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx)
        layout_diff, state_diff = tabs.duplicate(layout, state)
        new_layout, new_state = ctl.apply(ctx, layout, widget, layout_diff, state_diff)
        assert len(new_layout.tabs) == 2
        assert new_layout.tabs[0] == layout.tabs[0]
        assert new_layout.tabs[0] == new_layout.tabs[1]
    finally:
        app.shutdown()


def test_modify():
    ctx = Context(command_hub=CommandHub())
    inner_layout = make_inner_layout()
    outer_layout = make_outer_layout(inner_layout)
    inner_state = make_inner_state()
    outer_state = make_outer_state(inner_state)
    app = QtWidgets.QApplication()
    try:
        ctl = tabs.TabsCtl.from_piece(outer_layout)
        widget = ctl.construct_widget(outer_state, ctx)
        inner_layout_diff, inner_state_diff = tabs.duplicate(inner_layout, inner_state)
        outer_layout_diff, outer_state_diff = ctl._wrapper(
            wrapper=lambda x: x,
            idx=0,
            diffs=(inner_layout_diff, inner_state_diff),
            )
        new_outer_layout, new_outer_state = ctl.apply(
            ctx, outer_layout, widget, outer_layout_diff, outer_state_diff)
        assert len(new_outer_layout.tabs) == 1
        new_inner_layout = web.summon(new_outer_layout.tabs[0].ctl)
        assert len(new_inner_layout.tabs) == 2
        assert new_inner_layout.tabs[0] == inner_layout.tabs[0]
        assert new_inner_layout.tabs[0] == new_inner_layout.tabs[1]
    finally:
        app.shutdown()
