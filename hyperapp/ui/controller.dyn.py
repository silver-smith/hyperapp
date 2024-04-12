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
    view_creg,
    web,
    )
from .code.context import Context
from .code.list_diff import ListDiff
from .code.view import View, ReplaceViewDiff

log = logging.getLogger(__name__)


class CallbackFlag:

    def __init__(self):
        self.is_enabled = True

    @contextmanager
    def disabled(self):
        self.is_enabled = False
        try:
            yield
        finally:
            self.is_enabled = True

        
@dataclass
class _Item:
    _counter: itertools.count
    _callback_flag: CallbackFlag
    _id_to_item: dict[int, Self]

    id: int
    path: list[int]
    parent: Self | None
    ctx: Context
    name: str
    view: View
    focusable: bool
    _current_child_idx: int | None = None
    _widget: Any | None = None
    _commands: list[Self] = None
    _children: list = None

    def __repr__(self):
        return f"<{self.__class__.__name__.lstrip('_')} #{self.id} @{'/'.join(map(str, self.path))}: {self.view.__class__.__name__}>"

    @property
    def idx(self):
        return self.parent.children.index(self)

    @property
    def children(self):
        if self._children is None:
            self._children = []
            for idx, rec in enumerate(self.view.items()):
                item_id = next(self._counter)
                item = _Item(self._counter, self._callback_flag, self._id_to_item,
                             item_id, [*self.path, idx], self, self.ctx, rec.name, rec.view, rec.focusable)
                item.view.set_controller_hook(CtlHook(item))
                self._children.append(item)
                self._id_to_item[item_id] = item
        return self._children
                
    @property
    def current_child_idx(self):
        if self._current_child_idx is None:
            self._current_child_idx = self.view.get_current(self.widget)
        return self._current_child_idx

    @property
    def widget(self):
        if not self._widget:
            self._widget = self.parent.get_child_widget(self.idx)
            self.view.init_widget(self._widget)
        return self._widget

    @property
    def commands(self):
        if self._commands is None:
            self._commands = self._make_commands()
        return self._commands

    def _make_commands(self):
        return self._make_view_commands(self.view)

    def _make_view_commands(self, view):
        wrapper = self._apply_diff
        return [
            *ui_command_factory(view, self.widget, [wrapper]),
            *view.get_commands(self.widget, [wrapper]),
            ]

    def get_child_widget(self, idx):
        return self.view.item_widget(self.widget, idx)

    def _apply_diff(self, diff):
        if diff is None:
            return
        log.info("Apply diff to item #%d @ %s: %s", self.id, self.path, diff)
        with self._callback_flag.disabled():
            if isinstance(diff.piece, ReplaceViewDiff):
                self._apply_replace_view_diff(diff)
            else:
                self.view.apply(self.ctx, self.widget, diff)
            self._current_child_idx = None

    def _apply_replace_view_diff(self, diff):
        log.info("Replace view: %s", diff)
        self._children = None
        parent = self.parent
        idx = self.idx
        new_view = view_creg.animate(diff.piece.piece)
        new_widget = new_view.construct_widget(diff.state, self.ctx)
        parent.view.replace_child(parent.widget, idx, new_view, new_widget)

    def update_commands(self):

        def visit_item(item, commands):
            commands = [*item.commands, *commands]
            item.view.set_commands(item.widget, commands)
            for kid in item.children:
                if not kid.focusable:
                    kid.view.set_commands(kid.widget, commands)
            return commands

        def visit_item_and_children(item):
            if item.children:
                commands = visit_item_and_children(item.children[item.current_child_idx])
            else:
                commands = []
            commands = visit_item(item, commands)
            return commands

        def visit_parents(item, commands):
            if not item.parent:
                return
            if item.parent.current_child_idx != item.idx:
                return
            commands = visit_item(item.parent, commands)
            visit_parents(item.parent, commands)

        commands = visit_item_and_children(self)
        visit_parents(self, commands)

    def replace_item_element_hook(self, idx, new_view, new_widget):
        self._children = None

    def state_changed_hook(self):
        asyncio.create_task(self._state_changed_async())

    def current_changed_hook(self):
        if not self._callback_flag.is_enabled:
            return
        log.info("Controller: current changed: %s", self)
        self._current_child_idx = None
        self.update_commands()

    def commands_changed_hook(self):
        log.info("Controller: commands changed for: %s", self)
        self._commands = None
        self.update_commands()

    def element_inserted_hook(self, idx):
        self._children = None
        self._current_child_idx = None
        self.update_commands()

    def apply_diff_hook(self, diff):
        self._apply_diff(diff)

    async def _state_changed_async(self):
        if not self._callback_flag.is_enabled:
            return
        log.info("Controller: state changed for: %s", self)
        item = self.parent
        while item:
            await item.view.child_state_changed(item.ctx, item.widget)
            item = item.parent

    def replace_parent_widget_hook(self, new_widget):
        parent = self.parent
        parent.view.replace_child_widget(parent.widget, self.idx, new_widget)
        self._widget = None
        self._commands = None
        self.update_commands()


@dataclass(repr=False)
class _WindowItem(_Item):

    _window_items: list[Self] = None

    @classmethod
    def from_refs(cls, counter, callback_flag, id_to_item, ctx, window_items, view_ref, state_ref):
        view = view_creg.invite(view_ref)
        state = web.summon(state_ref)
        item_id = next(counter)
        widget = view.construct_widget(state, ctx)
        self = cls(counter, callback_flag, id_to_item, item_id, [item_id], None, ctx, f"window#{item_id}", view,
                   focusable=True, _window_items=window_items, _widget=widget)
        self._widget = widget
        self.view.set_controller_hook(CtlHook(self))
        id_to_item[item_id] = self
        return self

    def _make_commands(self):
        return self._make_view_commands(view=RootView(self._window_items, self.id))

    def _apply_diff(self, diff):
        log.info("Apply root diff: %s", diff)
        if isinstance(diff.piece, ListDiff.Insert):
            piece_ref = diff.piece.item
            state_ref = diff.state.item
            item = self.from_refs(self._counter, self._callback_flag, self._id_to_item, self.ctx, self._window_items, piece_ref, state_ref)
            self._window_items.insert(diff.piece.idx, item)
            item.update_commands()
            item.widget.show()
        else:
            raise NotImplementedError(diff.piece)


def _description(piece):
    return str(piece._t)


class RootView(View):

    def __init__(self, window_items, window_item_id):
        self._window_items = window_items
        self._window_item_id = window_item_id

    @property
    def piece(self):
        return htypes.root.view(
            window_list=[
                mosaic.put(item.view.piece)
                for item in self._window_items
                ],
            )

    def construct_widget(self, state, ctx):
        raise NotImplementedError()

    def widget_state(self, widget):
        window_list = [
            mosaic.put(item.view.widget_state(item.widget))
            for item in self._window_items
            ]
        current_idx = self._window_id_to_idx(self._window_item_id)
        return htypes.root.state(window_list, current_idx)

    def _window_id_to_idx(self, item_id):
        for idx, item in enumerate(self._window_items):
            if item.id == item_id:
                return idx
        raise RuntimeError(f"Unknown window item id: {item_id}")


class CtlHook:

    def __init__(self, item):
        self._item = item

    def commands_changed(self):
        self._item.commands_changed_hook()

    def current_changed(self):
        self._item.current_changed_hook()

    def state_changed(self):
        self._item.state_changed_hook()

    def element_inserted(self, idx):
        self._item.element_inserted_hook(idx)

    def replace_item_element(self, idx, new_view, new_widget=None):
        self._item.replace_item_element_hook(idx, new_view, new_widget)

    def replace_parent_widget(self, new_widget):
        self._item.replace_parent_widget_hook(new_widget)

    def apply_diff(self, diff):
        self._item.apply_diff_hook(diff)


class Controller:

    def __init__(self):
        self._window_items = None
        self._root_ctx = None
        self._id_to_item = None
        self._callback_flag = CallbackFlag()
        self._counter = itertools.count(start=1)

    def create_windows(self, root_piece, state, ctx, show=True):
        self._root_ctx = ctx
        self._window_items = []
        self._id_to_item = {}
        for piece_ref, state_ref in zip(root_piece.window_list, state.window_list):
            item = _WindowItem.from_refs(
                self._counter, self._callback_flag, self._id_to_item, ctx, self._window_items, piece_ref, state_ref)
            item.update_commands()
            if show:
                item.widget.show()
            self._window_items.append(item)

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
    context_kind_d = htypes.ui.context_model_command_kind_d()
    if current_item:
        commands = [
            cmd.clone_with_d(context_kind_d)
            for cmd
            in controller.item_commands(current_item.id)
            ]
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
