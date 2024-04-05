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
from .code.view import View, ReplaceViewDiff

log = logging.getLogger(__name__)


@dataclass
class _Item:
    id: int
    path: list[int]
    parent: Self | None
    ctx: Context
    name: str
    view: View
    focusable: bool
    current_child_idx: int
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

    def replace_parent_widget(self, new_widget):
        self._ctl.replace_parent_widget_hook(self._item, new_widget)

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
        widget = view.construct_widget(state, ctx)
        item = self._make_window_item(ctx, view, widget)
        return item

    def _set_window_commands(self, item):
        commands = self._collect_item_commands(item)
        root_wrapper = self._apply_root_diff
        commands += self._make_view_commands(RootView(self, item.id), item.widget, root_wrapper)
        self._update_aux_children_commands(item, old_commands=[], new_commands=commands)

    def _make_window_item(self, window_ctx, view, widget):
        item_id = next(self._counter)
        path = [item_id]
        item = self._populate_item(item_id, path, window_ctx, f"window#{item_id}", view)
        self._set_item_widget(item, widget)
        return item

    def _populate_item(self, item_id, path, ctx, name, view, focusable=True, parent=None):
        item = _Item(item_id, path, parent, ctx, name, view, focusable,
                     current_child_idx=0, widget=None, commands=None, children=[])
        for idx, rec in enumerate(view.items()):
            child_id = next(self._counter)
            child = self._populate_item(
                child_id, [*path, idx], ctx, rec.name, rec.view, rec.focusable, parent=item)
            item.children.append(child)
        self._id_to_item[item_id] = item
        view.set_controller_hook(CtlHook(self, item))
        return item

    def _set_item_widget(self, item, widget):
        item.widget = widget
        item.commands = self._make_item_commands(item, item.view, widget)
        item.current_child_idx = item.view.get_current(widget)
        item.view.init_widget(widget)
        current_child_commands = []
        for idx, child in enumerate(item.children):
            commands = self._set_item_widget(child, item.view.item_widget(widget, idx))
            if idx == item.current_child_idx:
                current_child_commands = commands
        sub_commands = item.commands + current_child_commands
        item.view.commands_changed(widget, [], sub_commands)
        self._update_aux_children_commands(item, [], sub_commands)
        return sub_commands

    def _make_item_commands(self, item, view, widget):
        wrapper = partial(self._apply_item_diff, item)
        return self._make_view_commands(view, widget, wrapper)

    def _make_view_commands(self, view, widget, wrapper):
        return [
            *ui_command_factory(view, widget, [wrapper]),
            *view.get_commands(widget, [wrapper]),
            ]

    def _replace_child_item_view(self, parent, idx, child_view):
        old_child = parent.children[idx]
        child_id = next(self._counter)
        child = self._populate_item(
            child_id, old_child.path, old_child.ctx, old_child.name, child_view, old_child.focusable, parent=parent)
        parent.children[idx] = child
        return child

    def _replace_child_item(self, parent, idx, child_view, child_widget):
        old_child = parent.children[idx]
        old_commands = self._collect_item_commands(old_child)
        new_child = self._replace_child_item_view(parent, idx, child_view)
        new_commands = self._collect_item_commands(new_child)
        self._set_item_widget(new_child, child_widget)
        self._update_item_commands(new_child, old_commands, new_commands)

    def _update_parents_commands(self, item, old_commands, new_commands):

        def update_item(item):
            item.view.commands_changed(item.widget, old_commands, new_commands)

        def update_parents(item):
            update_item(item)
            if not item.parent:
                return
            for sibling in item.parent.children:
                if not sibling.focusable:
                    # Update commands for aux views - command pane and menu bar are such views
                    update_item(sibling)
            update_parents(item.parent)

        update_parents(item)

    def _update_children_commands(self, item, old_commands, new_commands):

        def update_children(parent):
            for item in parent.children:
                item.view.commands_changed(item.widget, old_commands, new_commands)
                update_children(item)

        update_children(item)

    def _update_aux_children_commands(self, item, old_commands, new_commands):

        def update_children(parent):
            for item in parent.children:
                if item.focusable:
                    continue
                item.view.commands_changed(item.widget, old_commands, new_commands)
                update_children(item)

        update_children(item)

    def _update_item_commands(self, item, old_commands, new_commands):
        self._update_children_commands(item, old_commands, new_commands)
        self._update_parents_commands(item, old_commands, new_commands)

    def _collect_item_commands(self, item):
        commands = item.commands
        if item.children:
            idx = item.view.get_current(item.widget)
            commands = [*commands, *self._collect_item_commands(item.children[idx])]
        return commands

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
        new_idx = item.view.get_current(item.widget)
        log.info("Controller: current changed: #%d -> #%d for: %s", item.current_child_idx, new_idx, item)
        old_commands = self._collect_item_commands(item.children[item.current_child_idx])
        new_commands = self._collect_item_commands(item.children[new_idx])
        item.current_child_idx = new_idx
        self._update_parents_commands(item, old_commands, new_commands)

    def commands_changed_hook(self, item):
        log.info("Controller: commands changed for: %s", item)
        old_commands = item.commands
        new_commands = self._make_item_commands(item, item.view, item.widget)
        item.commands = new_commands
        self._update_item_commands(item, old_commands, new_commands)

    def state_changed_hook(self, item):
        asyncio.create_task(self._on_state_changed_async(item))

    def item_element_inserted(self, parent, idx):
        old_commands = self._collect_item_commands(parent.children[parent.current_child_idx])
        child_id = next(self._counter)
        rec = parent.view.items()[idx]
        child = self._populate_item(
            child_id, [*parent.path, idx], parent.ctx, rec.name, rec.view, rec.focusable, parent=parent)
        parent.children.insert(idx, child)
        self._set_item_widget(child, parent.view.item_widget(parent.widget, idx))
        new_commands = self._collect_item_commands(child)
        self._update_parents_commands(parent, old_commands, new_commands)
        self._update_children_commands(child, [], new_commands)

    def replace_item_element_hook(self, parent, idx, new_view, new_widget):
        old_commands = self._collect_item_commands(parent.children[idx])
        new_child = self._replace_child_item_view(parent, idx, new_view)
        if new_widget:
            self._set_item_widget(new_child, new_widget)
            new_commands = self._collect_item_commands(new_child)
            self._update_item_commands(new_child, old_commands, new_commands)

    def replace_parent_widget_hook(self, item, new_widget):
        parent = item.parent
        child_idx = item.path[-1]
        old_commands = self._collect_item_commands(item)
        parent.view.replace_child_widget(parent.widget, child_idx, new_widget)
        self._set_item_widget(item, new_widget)
        new_commands = self._collect_item_commands(item)
        self._update_item_commands(item, old_commands, new_commands)

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
            if isinstance(diff.piece, ReplaceViewDiff):
                self._apply_replace_view_diff(item, diff)
            else:
                item.view.apply(item.ctx, item.widget, diff)
            item.current_child_idx = item.view.get_current(item.widget)

    def _apply_replace_view_diff(self, item, diff):
        log.info("Replace view: %s", diff)
        idx = self._find_parent_idx(item)
        view = ui_ctl_creg.animate(diff.piece.piece)
        self._replace_child_item_view(item.parent, idx, view)

    def _find_parent_idx(self, item):
        for idx, kid in enumerate(item.parent.children):
            if kid is item:
                return idx
        raise RuntimeError(f"item {item} is not present in it's parent children")

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
