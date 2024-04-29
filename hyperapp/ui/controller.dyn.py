import asyncio
import itertools
import logging
import weakref
from collections import defaultdict, namedtuple
from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
from typing import Any, Self

from hyperapp.common import dict_coders  # register codec

from . import htypes
from .services import (
    feed_factory,
    mosaic,
    ui_command_factory,
    ui_model_command_factory,
    view_creg,
    web,
    )
from .code.context import Context
from .code.list_diff import ListDiff
from .code.tree_diff import TreeDiff
from .code.view import View

log = logging.getLogger(__name__)


def _ensure_diff_list(diffs):
    if diffs is None:
        return []
    if type(diffs) is list:
        return diffs
    else:
        return [diffs]


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
    _feed: Any

    id: int
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
        return f"<{self.__class__.__name__.lstrip('_')} #{self.id}: {self.view.__class__.__name__}>"

    @property
    def idx(self):
        return self.parent.children.index(self)

    @property
    def path(self):
        return [*self.parent.path, self.idx]

    @property
    def children(self):
        if self._children is None:
            self._children = []
            for rec in self.view.items():
                item = self._make_child_item(rec)
                self._children.append(item)
        return self._children

    def _make_child_item(self, rec):
        item_id = next(self._counter)
        item = _Item(self._counter, self._callback_flag, self._id_to_item, self._feed,
                     item_id, self, self.ctx, rec.name, rec.view, rec.focusable)
        item.view.set_controller_hook(CtlHook(item))
        self._id_to_item[item_id] = item
        return item

    @property
    def current_child_idx(self):
        if self._current_child_idx is None:
            self._current_child_idx = self.view.get_current(self.widget)
        return self._current_child_idx

    @property
    def current_child(self):
        idx = self.current_child_idx
        if idx is None:
            return None
        return self.children[idx]

    @property
    def widget(self):
        if not self._widget:
            self._widget = self.parent.get_child_widget(self.idx)
            self._widget = self.parent.get_child_widget(self.idx)
            self.view.init_widget(self._widget)
        return self._widget

    @property
    def model(self):
        return self.view.get_model()

    @property
    def navigator(self):

        def parent_navigator(item):
            if item.view and item.view.is_navigator:
                return item.view
            if not item.parent:
                return None
            return parent_navigator(item.parent)

        def child_navigator(item):
            child = item.current_child
            if child is None:
                return None
            if child.view.is_navigator:
                return child
            return child_navigator(child)

        navigator = parent_navigator(self)
        if navigator:
            return navigator
        return child_navigator(self)

    @property
    def commands(self):
        if self._commands is None:
            self._commands = self._make_commands()
        return self._commands

    def _make_commands(self):
        ctx = self._command_context()
        commands = ui_command_factory(self.view, ctx)
        if 'piece' not in ctx:
            return commands
        return commands + ui_model_command_factory(ctx.piece, ctx.model_state, ctx)

    def _command_context(self):
        ctx = self.ctx.clone_with(
            view=self.view,
            widget=weakref.ref(self.widget),
            navigator=self.navigator,
            )
        model = self.model
        if model is None:
            return ctx
        model_state = self.view.model_state(self.widget)
        return ctx.clone_with(
            piece=model,
            model_state=model_state,
            **self.ctx.attributes(model_state),
            )

    def get_child_widget(self, idx):
        return self.view.item_widget(self.widget, idx)

    def _apply_diff(self, diffs):
        diff_list = _ensure_diff_list(diffs)
        with self._callback_flag.disabled():
            for diff in diff_list:
                log.info("Apply diff to item #%d @ %s: %s", self.id, self.path, diff)
                self.view.apply(self.ctx, self.widget, diff)
                self._current_child_idx = None

    def _apply_replace_view_diff(self, diff):
        log.info("Replace view @%s: %s", self, diff)
        parent = self.parent
        idx = self.idx
        parent._children = None
        new_view = view_creg.animate(diff.piece.piece, self.ctx)
        new_widget = new_view.construct_widget(diff.state, self.ctx)
        parent.view.replace_child(parent.widget, idx, new_view, new_widget)

    def update_model(self):

        def visit_item(item, model):
            item_model = item.view.get_model()
            if item_model is not None:
                model = item_model
            else:
                item.view.model_changed(item.widget, model)
            for kid in item.children:
                if not kid.focusable:
                    kid.view.model_changed(kid.widget, model)
            return model

        def visit_item_and_children(item):
            if item.children:
                model = visit_item_and_children(item.current_child)
            else:
                model = None
            return visit_item(item, model)

        def visit_parents(item, model):
            if not item.parent:
                return
            if item.parent.current_child_idx != item.idx:
                return
            model = visit_item(item.parent, model)
            visit_parents(item.parent, model)

        model = visit_item_and_children(self)
        visit_parents(self, model)

    def update_commands(self):

        def visit_item(item, commands):
            if item.view is None:
                return  # Root item.
            commands = [*item.commands, *commands]
            item.view.set_commands(item.widget, commands)
            for kid in item.children:
                if not kid.focusable:
                    kid.view.set_commands(kid.widget, commands)
            return commands

        def visit_item_and_children(item):
            if item.children:
                commands = visit_item_and_children(item.current_child)
            else:
                commands = []
            commands = visit_item(item, commands)
            return commands

        def visit_parents(item, commands):
            if not item.parent:
                return
            if (item.parent.current_child_idx is not None
                    and item.parent.current_child_idx != item.idx):
                return
            commands = visit_item(item.parent, commands)
            visit_parents(item.parent, commands)

        commands = visit_item_and_children(self)
        visit_parents(self, commands)

    def element_replaced_hook(self, idx, new_view, new_widget):
        view_items = self.view.items()
        item = self._make_child_item(view_items[idx])
        self._children[idx] = item

    def state_changed_hook(self):
        asyncio.create_task(self._state_changed_async())

    def current_changed_hook(self):
        if not self._callback_flag.is_enabled:
            return
        log.info("Controller: current changed: %s", self)
        self._current_child_idx = None
        self.update_commands()
        self.update_model()
        self.save_state()

    def commands_changed_hook(self):
        log.info("Controller: commands changed for: %s", self)
        self._commands = None
        self.update_commands()

    # Should be on stack for proper module for feed constructor be picked up.
    async def _send_model_diff(self, model_diff):
        await self._feed.send(model_diff)

    def element_inserted_hook(self, idx):
        self._children = None
        self._current_child_idx = None
        self.update_commands()
        self.update_model()
        self.save_state()
        item = self.children[idx]
        model_diff = TreeDiff.Insert(item.path, item.model_item)
        asyncio.create_task(self._send_model_diff(model_diff))

    def element_removed_hook(self, idx):
        self._children = None
        self._current_child_idx = None
        self.update_commands()
        self.update_model()
        self.save_state()

    def apply_diff_hook(self, diff):
        self._apply_diff(diff)

    async def _state_changed_async(self):
        if not self._callback_flag.is_enabled:
            return
        log.info("Controller: state changed for: %s", self)
        self._commands = None
        self.update_commands()
        item = self.parent
        while item:
            if item.view:
                await item.view.child_state_changed(item.ctx, item.widget)
            item = item.parent

    def replace_parent_widget_hook(self, new_widget):
        parent = self.parent
        parent.view.replace_child_widget(parent.widget, self.idx, new_widget)
        self._widget = None
        self._commands = None
        self.update_commands()
        self.update_model()
        self.save_state()
        model_diff = TreeDiff.Replace(self.path, self.model_item)
        asyncio.create_task(self._send_model_diff(model_diff))

    def save_state(self):
        self.parent.save_state()

    @property
    def model_item(self):
        return htypes.layout.item(self.id, self.name, self.focusable, _description(self.view.piece))


@dataclass(repr=False)
class _WindowItem(_Item):

    @classmethod
    def from_refs(cls, counter, callback_flag, id_to_item, feed, ctx, parent, view_ref, state_ref):
        view = view_creg.invite(view_ref, ctx)
        state = web.summon(state_ref)
        item_id = next(counter)
        self = cls(counter, callback_flag, id_to_item, feed,
                   item_id, parent, ctx, f"window#{item_id}", view, focusable=True)
        self._init(state)
        return self

    def _init(self, state):
        widget = self.view.construct_widget(state, self.ctx)
        self._widget = widget
        self.view.set_controller_hook(CtlHook(self))
        self._id_to_item[self.id] = self

    def _command_context(self):
        return super()._command_context().clone_with(
            root=Root(root_item=self.parent),
            )

    def save_state(self):
        self.parent.save_state(current_window=self)


@dataclass(repr=False)
class _RootItem(_Item):

    _layout_bundle: Any = None
    _show: bool = True

    @classmethod
    def from_piece(cls, counter, callback_flag, id_to_item, feed, show, ctx, layout_bundle, layout):
        item_id = 0
        self = cls(counter, callback_flag, id_to_item, feed, item_id, None, ctx, "root",
                   view=None, focusable=False, _layout_bundle=layout_bundle, _show=show)
        self._children = [
            _WindowItem.from_refs(
                counter, callback_flag, id_to_item, feed, ctx, self, piece_ref, state_ref)
            for piece_ref, state_ref
            in zip(layout.piece.window_list, layout.state.window_list)
            ]
        id_to_item[item_id] = self
        return self

    def show(self):
        for item in self._children:
            item.update_commands()
            item.update_model()
            item.widget.show()

    @property
    def path(self):
        return []

    @property
    def children(self):
        return self._children

    @property
    def current_child_idx(self):
        return None

    def save_state(self, current_window):
        layout = htypes.root.layout(
            piece=self._root_piece,
            state=self._root_state(current_window),
            )
        self._layout_bundle.save_piece(layout)

    @property
    def _root_piece(self):
        return htypes.root.view(
            window_list=tuple(
                mosaic.put(item.view.piece)
                for item in self.children
                ),
            )

    def _root_state(self, current_window):
        window_list = tuple(
            mosaic.put(item.view.widget_state(item.widget))
            for item in self.children
            )
        return htypes.root.state(window_list, current_window.idx)

    def create_window(self, piece, state):
        view = view_creg.animate(piece, self.ctx)
        item_id = next(self._counter)
        item = _WindowItem(self._counter, self._callback_flag, self._id_to_item, self._feed,
                           item_id, self, self.ctx, f"window#{item_id}", view, focusable=True)
        item._init(state)
        self._children.append(item)
        item.update_commands()
        item.update_model()
        if self._show:
            item.widget.show()
        self.save_state(item)
        model_diff = TreeDiff.Insert(item.path, item.model_item)
        asyncio.create_task(self._send_model_diff(model_diff))


def _description(piece):
    return str(piece._t)


class Root:

    def __init__(self, root_item):
        self._root_item = root_item

    def create_window(self, piece, state):
        self._root_item.create_window(piece, state)


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

    def element_removed(self, idx):
        self._item.element_removed_hook(idx)

    def element_replaced(self, idx, new_view, new_widget=None):
        self._item.element_replaced_hook(idx, new_view, new_widget)

    def replace_parent_widget(self, new_widget):
        self._item.replace_parent_widget_hook(new_widget)

    def apply_diff(self, diff):
        self._item.apply_diff_hook(diff)


class Controller:

    instance = None

    @classmethod
    @contextmanager
    def running(cls, layout_bundle, default_layout, ctx, show=False, load_state=False):
        cls.instance = self = cls(layout_bundle, default_layout, ctx, show, load_state)
        try:
            if show:
                self.show()
            yield self
        finally:
            cls.instance = None

    def __init__(self, layout_bundle, default_layout, ctx, show, load_state):
        self._root_ctx = ctx
        self._id_to_item = {}
        self._callback_flag = CallbackFlag()
        self._counter = itertools.count(start=1)
        self._feed = feed_factory(htypes.layout.view())
        layout = default_layout
        if load_state:
            try:
                layout = layout_bundle.load_piece()
            except FileNotFoundError:
                pass
        self._root_item = _RootItem.from_piece(
            self._counter, self._callback_flag, self._id_to_item, self._feed, show, ctx, layout_bundle, layout)

    def show(self):
        self._root_item.show()

    def view_items(self, item_id):
        item = self._id_to_item.get(item_id)
        if item:
            item_list = item.children
        else:
            item_list = []
        return [item.model_item for item in item_list]

    def item_commands(self, item_id):
        item = self._id_to_item.get(item_id)
        if item:
            return item.commands
        else:
            return []


def layout_tree(piece, parent):
    if parent is None:
        parent_id = 0
    else:
        parent_id = parent.id
    return Controller.instance.view_items(parent_id)


def layout_tree_commands(piece, current_item):
    context_kind_d = htypes.ui.context_model_command_kind_d()
    if current_item:
        commands = [
            cmd.clone_with_d(context_kind_d)
            for cmd
            in Controller.instance.item_commands(current_item.id)
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
        for command in Controller.instance.item_commands(piece.item_id)
        ]
    log.info("Get view item commands for %s: %s", piece, command_list)
    return command_list


async def add_view_command(piece, current_item):
    log.info("Add view command for %s: %s", piece, current_item)
