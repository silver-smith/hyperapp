import asyncio
import itertools
import logging
import weakref
from collections import defaultdict, namedtuple
from contextlib import contextmanager
from dataclasses import dataclass
from functools import cached_property, partial
from typing import Any, Self

from hyperapp.common import dict_coders  # register codec

from . import htypes
from .services import (
    ui_command_factory,
    deduce_t,
    feed_factory,
    mosaic,
    set_model_layout,
    list_view_commands,
    ui_model_command_factory,
    view_creg,
    web,
    )
from .code.context import Context
from .code.tree_diff import TreeDiff
from .code.view import View

log = logging.getLogger(__name__)


_NavigatorRec = namedtuple('_NavigatorRec', 'view widget_wr')


@dataclass
class CommandRec:
    piece: Any
    ctx: Any

    @cached_property
    def animated(self):
        return ui_command_factory(self.piece, self.ctx)

        
@dataclass
class _Item:
    _counter: itertools.count
    _id_to_item: dict[int, Self]
    _feed: Any

    id: int
    parent: Self | None
    ctx: Context
    rctx: Context  # Parent-context from children.
    name: str
    view: View
    focusable: bool
    _current_child_idx: int | None = None
    _widget_wr: Any | None = None
    _view_commands: list[CommandRec] | None = None
    _model_commands: list[CommandRec] | None = None
    _children: list[Self] | None = None

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
        ctx = rec.view.children_context(self.ctx)
        item = _Item(self._counter, self._id_to_item, self._feed,
                     item_id, self, ctx, None, rec.name, rec.view, rec.focusable)
        item.view.set_controller_hook(item._hook)
        self._id_to_item[item_id] = item
        return item

    @property
    def _hook(self):
        return CtlHook(self)

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
        if not self._widget_wr:
            widget = self.parent.get_child_widget(self.idx)
            self._widget_wr = weakref.ref(widget)
            self.view.init_widget(widget)
        widget = self._widget_wr()
        if widget is None:
            raise RuntimeError("Widget is gone")
        return widget

    @property
    def model(self):
        return self.view.get_model()

    @property
    def navigator_item(self):

        def parent_navigator(item):
            if item.view and item.view.is_navigator:
                return item
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
    def navigator_rec(self):
        item = self.navigator_item
        if item:
            return _NavigatorRec(item.view, weakref.ref(item.widget))
        else:
            return None

    @property
    def view_commands(self):
        if self._view_commands is None:
            self._view_commands = self._make_view_commands()
        return self._view_commands

    @property
    def model_commands(self):
        if self._model_commands is None:
            self._model_commands = self._make_model_commands()
        return self._model_commands

    def _make_view_commands(self):
        ctx = self.command_context()
        commands = list_view_commands(self.view)
        return [CommandRec(cmd, ctx) for cmd in commands]

    def _make_model_commands(self):
        model = self.model
        if model is None:
            return []
        ctx = self._model_command_context(model)
        commands = ui_model_command_factory(ctx.piece, ctx)
        return [CommandRec(cmd, ctx) for cmd in commands]

    def command_context(self):
        ctx = self.ctx.push(
            view=self.view,
            widget=weakref.ref(self.widget),
            hook=self._hook,
            navigator=self.navigator_rec,
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

    def _model_command_context(self, model):
        ctx = self.command_context()
        model_state = self.view.model_state(self.widget)
        return ctx.clone_with(
            piece=model,
            model_state=model_state,
            **self.ctx.attributes(model_state),
            )

    def get_child_widget(self, idx):
        return self.view.item_widget(self.widget, idx)

    def _update_parents_context(self):
        asyncio.create_task(self.update_parents_context(self.rctx))

    async def update_parents_context(self, rctx):
        for idx, item in enumerate(self.children):
            if item.focusable and idx != self._current_child_idx:
                continue
            rctx = item.view.parent_context(rctx, item.widget)
        self.rctx = rctx
        await self.view.children_context_changed(self.ctx, rctx, self.widget)
        rctx = self._reverse_context(rctx)
        if self.parent and parent.current_child is self:
            await self.parent.update_parents_context(rctx)

    def _reverse_context(self, rctx):
        rctx = self.view.parent_context(rctx, self.widget)
        kw = {'view_commands': self.view_commands}
        if self.model_commands:
            kw = {**kw, 'model_commands': self.model_commands}
        return rctx.clone_with(**kw)

    def parent_context_changed_hook(self):
        log.info("Controller: parent context changed from: %s", self)
        # Recreate commands because model_state may be changed.
        self._view_commands = None
        self._model_commands = None
        self._update_parents_context()

    def current_changed_hook(self):
        log.info("Controller: current changed from: %s", self)
        self._current_child_idx = None
        self._update_parents_context()
        self.save_state()

    # Should be on stack for proper module for feed constructor be picked up.
    async def _send_model_diff(self, model_diff):
        await self._feed.send(model_diff)

    def _set_model_layout(self, layout):
        model = self.rctx.model
        t = deduce_t(model)
        set_model_layout(self.ctx.lcs, t, layout)

    def _replace_child_item(self, idx):
        view_items = self.view.items()
        item = self._make_child_item(view_items[idx])
        self._children[idx] = item
        self._update_parents_context()
        self.save_state()
        model_diff = TreeDiff.Replace(self.path, self.model_item)
        asyncio.create_task(self._send_model_diff(model_diff))

    # Current navigator is changed, should update commands so their navigator be up-to-date.
    def _invalidate_parents_commands(self):
        self._view_commands = None
        self._model_commands = None
        if self.parent:
            self.parent._invalidate_parents_commands()

    def replace_view_hook(self, new_view, new_state=None):
        log.info("Controller: Replace view @%s -> %s", self, new_view)
        parent = self.parent
        idx = self.idx
        new_widget = new_view.construct_widget(new_state, self.ctx)
        parent.view.replace_child(parent.widget, idx, new_view, new_widget)
        parent._replace_child_item(idx)
        if parent.view.is_navigator:
            parent._set_model_layout(new_view.piece)

    def element_replaced_hook(self, idx, new_view, new_widget):
        log.info("Controller: Element replaced @%s #%d -> %s", self, idx, new_view)
        self._replace_child_item(idx)

    def element_inserted_hook(self, idx):
        view_items = self.view.items()
        item = self._make_child_item(view_items[idx])
        self._children.insert(idx, item)
        self._current_child_idx = None
        self._invalidate_parents_commands()
        self._update_parents_context()
        self.save_state()
        model_diff = TreeDiff.Insert(item.path, item.model_item)
        asyncio.create_task(self._send_model_diff(model_diff))

    def element_removed_hook(self, idx):
        del self._children[idx]
        self._current_child_idx = None
        self._invalidate_parents_commands()
        self._update_parents_context()
        self.save_state()

    def replace_parent_widget_hook(self, new_widget):
        parent = self.parent
        parent.view.replace_child_widget(parent.widget, self.idx, new_widget)
        self._widget_wr = None
        self._view_commands = None
        self._model_commands = None

    def save_state(self):
        self.parent.save_state()

    @property
    def model_item(self):
        return htypes.layout.item(self.id, self.name, self.focusable, _description(self.view.piece))


@dataclass(repr=False)
class _WindowItem(_Item):

    _window_widget: Any = None

    @classmethod
    def from_refs(cls, counter, id_to_item, feed, ctx, parent, view_ref, state_ref):
        view = view_creg.invite(view_ref, ctx)
        state = web.summon(state_ref)
        item_id = next(counter)
        self = cls(counter, id_to_item, feed,
                   item_id, parent, ctx, None, f"window#{item_id}", view, focusable=True)
        self._init(state)
        return self

    def _init(self, state):
        widget = self.view.construct_widget(state, self.ctx)
        self._widget_wr = weakref.ref(widget)
        self.view.set_controller_hook(self._hook)
        self._id_to_item[self.id] = self
        self._window_widget = widget  # Prevent windows refs from be gone.

    def command_context(self):
        return super().command_context().clone_with(
            root=Root(root_item=self.parent),
            )

    def save_state(self):
        self.parent.save_state(current_window=self)


@dataclass(repr=False)
class _RootItem(_Item):

    _layout_bundle: Any = None
    _show: bool = True

    @classmethod
    def from_piece(cls, counter, id_to_item, feed, show, ctx, layout_bundle, layout):
        item_id = 0
        self = cls(counter, id_to_item, feed, item_id, None, ctx, None, "root",
                   view=None, focusable=False, _layout_bundle=layout_bundle, _show=show)
        self._children = [
            _WindowItem.from_refs(
                counter, id_to_item, feed, ctx, self, piece_ref, state_ref)
            for piece_ref, state_ref
            in zip(layout.piece.window_list, layout.state.window_list)
            ]
        id_to_item[item_id] = self
        return self

    def show(self):
        for item in self._children:
            self._update_parents_context()
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
        ctx = view.children_context(self.ctx)
        item = _WindowItem(self._counter, self._id_to_item, self._feed,
                           item_id, self, ctx, None, f"window#{item_id}", view, focusable=True)
        item._init(state)
        self._children.append(item)
        self._update_parents_context()
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

    def current_changed(self):
        self._item.current_changed_hook()

    def parent_context_changed(self):
        self._item.parent_context_changed_hook()

    def replace_view(self, new_view, new_state=None):
        self._item.replace_view_hook(new_view, new_state)

    def element_inserted(self, idx):
        self._item.element_inserted_hook(idx)

    def element_removed(self, idx):
        self._item.element_removed_hook(idx)

    def element_replaced(self, idx, new_view, new_widget=None):
        self._item.element_replaced_hook(idx, new_view, new_widget)

    def replace_parent_widget(self, new_widget):
        self._item.replace_parent_widget_hook(new_widget)


class Controller:

    @classmethod
    @contextmanager
    def running(cls, layout_bundle, default_layout, ctx, show=False, load_state=False):
        self = cls(layout_bundle, default_layout, ctx, show, load_state)
        if show:
            self.show()
        yield self

    def __init__(self, layout_bundle, default_layout, ctx, show, load_state):
        self._root_ctx = ctx.clone_with(controller=self)
        self._id_to_item = {}
        self._counter = itertools.count(start=1)
        self._feed = feed_factory(htypes.layout.view())
        self._inside_commands_call = False
        layout = default_layout
        if load_state:
            try:
                layout = layout_bundle.load_piece()
            except FileNotFoundError:
                pass
        self._root_item = _RootItem.from_piece(
            self._counter, self._id_to_item, self._feed, show, self._root_ctx, layout_bundle, layout)

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
        if self._inside_commands_call:
            return []
        self._inside_commands_call = True
        try:
            item = self._id_to_item.get(item_id)
            if item:
                return [rec.piece for rec in item.view_commands + item.model_commands]
            else:
                return []
        finally:
            self._inside_commands_call = False

    def item_command_context(self, item_id):
        item = self._id_to_item[item_id]
        return item.command_context()
