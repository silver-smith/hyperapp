import asyncio
import itertools
import logging
from collections import defaultdict, namedtuple
from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
from typing import Any, Self

from . import htypes
from .services import (
    mosaic,
    ui_command_factory,
    ui_ctl_creg,
    web,
    )
from .code.context import Context
from .code.list_diff import ListDiff
from .code.view import View
from .code.command_hub import CommandHub

log = logging.getLogger(__name__)


@dataclass
class _Item:
    id: int
    path: list[int]
    parent: Self | None
    ctx: Context
    command_hub: CommandHub
    name: str
    view: View
    focusable: bool
    widget: Any
    commands: list
    children: list


def _description(piece):
    return str(piece._t)


class RootView(View):

    def __init__(self, controller, window_item_id):
        self._controller = controller
        self._window_item_id = window_item_id

    @property
    def piece(self):
        return self._controller.root_piece

    def construct_widget(self, state, ctx):
        raise NotImplementedError()

    def widget_state(self, widget):
        current_idx = self._controller.window_id_to_idx(self._window_item_id)
        return htypes.root.state(self._controller.get_window_state_list(), current_idx)


class CtlHook:

    def __init__(self, ctl, item):
        self._ctl = ctl
        self._item = item

    def commands_changed(self):
        self._ctl.commands_changed_hook(self._item)

    def item_changed(self):
        self._ctl.item_changed_hook(self._item)

    def child_changed(self, idx, view, widget):
        self._ctl.child_changed_hook(self._item, idx, view, widget)

    def current_changed(self):
        self._ctl.current_changed_hook(self._item)

    def state_changed(self):
        self._ctl.state_changed_hook(self._item)

    def item_element_inserted(self, idx):
        self._ctl.item_element_inserted(self._item, idx)

    def replace_item_element(self, idx, new_view, new_widget=None):
        self._ctl.replace_item_element_hook(self._item, idx, new_view, new_widget)

    def apply_diff(self, diff):
        self._ctl.apply_diff_hook(self._item, diff)


class Controller:

    def __init__(self):
        self._window_items = None
        self._root_ctx = None
        self._id_to_item = None
        self._run_callback = True
        self._counter = itertools.count(start=1)

    def create_windows(self, root_piece, state, ctx, show=True):
        self._root_ctx = ctx
        self._id_to_item = {}
        self._window_items = [
            self._create_window(piece_ref, state_ref, ctx)
            for piece_ref, state_ref
            in zip(root_piece.window_list, state.window_list)
            ]
        for item in self._window_items:
            self._set_window_commands(item)
            if show:
                item.widget.show()

    def get_window_state_list(self):
        return [
            mosaic.put(item.view.widget_state(item.widget))
            for item in self._window_items
            ]

    def window_id_to_idx(self, item_id):
        for idx, item in enumerate(self._window_items):
            if item.id == item_id:
                return idx
        raise RuntimeError(f"Unknown window item id: {item_id}")

    @property
    def root_piece(self):
        return htypes.root.view(
            window_list=[
                mosaic.put(item.view.piece)
                for item in self._window_items
                ],
            )
    
    def _create_window(self, piece_ref, state_ref, ctx):
        view = ui_ctl_creg.invite(piece_ref)
        state = web.summon(state_ref)
        command_hub = CommandHub()
        window_ctx = ctx.clone_with(command_hub=command_hub)
        widget = view.construct_widget(state, window_ctx)
        item = self._make_window_item(window_ctx, command_hub, view, widget)
        return item

    def _set_window_commands(self, item):
        path_to_commands = self._collect_item_commands(item)
        root_wrapper = self._apply_root_diff
        root_commands = self._make_view_commands(RootView(self, item.id), item.widget, root_wrapper)
        path_to_commands = {
            (): root_commands,
            **path_to_commands,
            }
        item.command_hub.set_commands(path_to_commands)

    def _make_window_item(self, window_ctx, command_hub, view, widget):
        item_id = next(self._counter)
        path = [item_id]
        item = self._populate_item(item_id, path, window_ctx, command_hub, f"window#{item_id}", view)
        self._set_item_widget(item, widget)
        return item

    def _populate_item(self, item_id, path, ctx, command_hub, name, view, focusable=True, parent=None):
        item = _Item(item_id, path, parent, ctx, command_hub, name, view, focusable, widget=None, commands=None, children=[])
        for idx, rec in enumerate(view.items()):
            child_id = next(self._counter)
            child = self._populate_item(
                child_id, [*path, idx], ctx, command_hub, rec.name, rec.view, rec.focusable, parent=item)
            item.children.append(child)
        self._id_to_item[item_id] = item
        view.set_controller_hook(CtlHook(self, item))
        return item

    def _set_item_widget(self, item, widget):
        item.widget = widget
        item.commands = self._make_item_commands(item, item.view, widget)
        item.view.init_widget(widget)
        for idx, child in enumerate(item.children):
            self._set_item_widget(child, item.view.item_widget(widget, idx))

    def _make_item_commands(self, item, view, widget):
        wrapper = partial(self._apply_item_diff, item)
        return self._make_view_commands(view, widget, wrapper)

    def _make_view_commands(self, view, widget, wrapper):
        return [
            *ui_command_factory(view, widget, [wrapper]),
            *view.get_commands(widget, [wrapper]),
            ]

    def _replace_child_item_view(self, item, idx, view):
        old_child = item.children[idx]
        child_id = next(self._counter)
        child = self._populate_item(
            child_id, old_child.path, old_child.ctx, old_child.command_hub, old_child.name, view, old_child.focusable, parent=item)
        item.children[idx] = child
        return child

    def _replace_child_item(self, item, idx, view, widget):
        child = self._replace_child_item_view(item, idx, view)
        self._set_item_widget(child, widget)
        self._update_item_commands(child)

    def _update_item_commands(self, item):
        path_to_commands = self._collect_item_commands(item)
        item.command_hub.set_commands(path_to_commands)

    def item_changed_hook(self, item):
        log.info("Item is changed: %s", item)
        idx = item.parent.children.index(item)
        self._replace_child_item(item.parent, idx, item.view, item.widget)

    def child_changed_hook(self, item, idx, view, widget):
        log.info("Child #%d changed for: %s", idx, item)
        self._replace_child_item(item, idx, view, widget)

    def current_changed_hook(self, item):
        if not self._run_callback:
            return
        idx = item.view.get_current(item.widget)
        log.info("Controller: current changed to #%d for: %s", idx, item)
        self._update_item_commands(item.children[idx])

    def commands_changed_hook(self, item):
        log.info("Controller: commands changed for: %s", item)
        item.commands[:] = self._make_item_commands(item, item.view, item.widget)
        self._update_item_commands(item)

    def state_changed_hook(self, item):
        asyncio.create_task(self._on_state_changed_async(item))

    def item_element_inserted(self, item, idx):
        child_id = next(self._counter)
        rec = item.view.items()[idx]
        child = self._populate_item(
            child_id, [*item.path, idx], item.ctx, item.command_hub, rec.name, rec.view, rec.focusable, parent=item)
        item.children.insert(idx, child)
        self._set_item_widget(child, item.view.item_widget(item.widget, idx))
        self._update_item_commands(child)

    def replace_item_element_hook(self, item, idx, new_view, new_widget):
        child = self._replace_child_item_view(item, idx, new_view)
        if new_widget:
            self._set_item_widget(child, new_widget)
            self._update_item_commands(child)

    def apply_diff_hook(self, item, diff):
        self._apply_item_diff(item, diff)

    async def _on_state_changed_async(self, item):
        if not self._run_callback:
            return
        log.info("Controller: state changed for: %s", item)
        item = item.parent
        while item:
            await item.view.child_state_changed(item.ctx, item.widget)
            item = item.parent

    def _collect_item_commands(self, item):
        path_to_commands = {tuple(item.path): item.commands}
        if item.children:
            idx = item.view.get_current(item.widget)
            path_to_commands.update(self._collect_item_commands(item.children[idx]))
        return path_to_commands
        
    @contextmanager
    def _without_callback(self):
        self._run_callback = False
        try:
            yield
        finally:
            self._run_callback = True

    def _apply_item_diff(self, item, diff):
        if diff is None:
            return
        log.info("Apply diff to item #%d @ %s: %s", item.id, item.path, diff)
        with self._without_callback():
            replace_widget = item.view.apply(item.ctx, item.widget, diff)
            log.info("Applied diff, should replace widget: %s", replace_widget)
            if not replace_widget:
                return
            parent = item.parent
            child_idx = item.path[-1]
            new_widget = parent.view.replace_widget(parent.ctx, parent.widget, child_idx)
            self._set_item_widget(item, new_widget)
            self._update_item_commands(item)

    def _apply_root_diff(self, diff):
        log.info("Apply root diff: %s", diff)
        if isinstance(diff.piece, ListDiff.Insert):
            piece_ref = diff.piece.item
            state_ref = diff.state.item
            item = self._create_window(piece_ref, state_ref, self._root_ctx)
            self._window_items = diff.piece.insert(self._window_items, item)
            self._set_window_commands(item)
            item.widget.show()
        else:
            raise NotImplementedError(diff.piece)

    def view_items(self, item_id):
        if item_id == 0:
            item_list = self._window_items
        else:
            item = self._id_to_item.get(item_id)
            if item:
                item_list = item.children
            else:
                item_list = []
        return [
            htypes.layout.item(item.id, item.name, item.focusable, _description(item.view.piece))
            for item in item_list
            ]

    def item_commands(self, item_id):
        item = self._id_to_item.get(item_id)
        if item:
            return item.commands
        else:
            return []


controller = Controller()


def layout_tree(piece, parent):
    if parent is None:
        parent_id = 0
    else:
        parent_id = parent.id
    return controller.view_items(parent_id)


def layout_tree_commands(piece, current_item):
    if current_item:
        commands = controller.item_commands(current_item.id)
    else:
        commands = []
    log.info("Layout tree commands for %s: %s", current_item, commands)
    return commands


async def open_layout_tree():
    return htypes.layout.view()


async def open_view_item_commands(piece, current_item):
    log.info("Open view item commands for: %s", current_item)
    if current_item:
        return htypes.layout.command_list(item_id=current_item.id)


def view_item_commands(piece):
    command_list = [
        htypes.layout.command_item(command.name)
        for command in controller.item_commands(piece.item_id)
        ]
    log.info("Get view item commands for %s: %s", piece, command_list)
    return command_list


async def add_view_command(piece, current_item):
    log.info("Add view command for %s: %s", piece, current_item)
