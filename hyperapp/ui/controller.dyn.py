import asyncio
import itertools
import logging
import weakref
from collections import namedtuple
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import cached_property, partial
from typing import Any, Self

# from PySide6 import QtGui

from hyperapp.boot import dict_coders  # register codec

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    web,
    )
from .code.mark import mark
from .code.context import Context
from .code.tree_diff import TreeDiff
from .code.view import View

log = logging.getLogger(__name__)


# Services used by controller and it's items.
CtlServices = namedtuple(
    'CtlServices', [
        'feed_factory',
        'view_reg',
        'get_view_commands',
        'get_view_element_commands',
        'get_ui_model_commands',
        ])

# attributes shared by all items.
ItemMeta = namedtuple('ItemMeta', 'svc counter id_to_item feed')


@dataclass
class _Item:
    _meta: ItemMeta

    id: int
    parent: Self | None
    ctx: Context
    name: str
    view: View
    focusable: bool
    view_commands: list = None  # Bound commands.
    _current_child_idx: int | None = None
    _widget_wr: Any | None = None
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
            if self.view:
                for rec in self.view.items():
                    item = self._make_child_item(rec)
                    self._children.append(item)
        return self._children

    def pick_child(self, path):
        if not path:
            return self
        idx, *rest = path
        if idx < len(self.children):
            return self.children[idx].pick_child(rest)
        return None

    def _make_child_item(self, rec):
        item_id = next(self._meta.counter)
        ctx = self.view.children_context(self.ctx)
        item = _Item(self._meta, item_id, self, ctx, rec.name, rec.view, rec.focusable)
        if item.view:
            item.view.set_controller_hook(item.hook)
        self._meta.id_to_item[item_id] = item
        return item

    @property
    def hook(self):
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
        if self._widget_wr:
            widget = self._widget_wr()
            if widget is None:
                raise RuntimeError("Widget is gone")
        else:
            widget = self._init_widget()
        return widget

    def _init_widget(self):
        if not self.view:
            return
        if self._widget_wr:
            return
        widget = self.parent.get_child_widget(self.idx)
        self._widget_wr = weakref.ref(widget)
        self.view.init_widget(widget, self.focusable)
        return widget

    def get_child_widget(self, idx):
        return self.view.item_widget(self.widget, idx)

    def children_changed(self):
        self.parent.children_changed()

    async def update_children(self):
        kid = self.current_child
        if kid:
            rctx = await kid.update_children()
        else:
            rctx = Context()
        await self.view.children_changed(self.ctx, rctx, self.widget)
        self.view_commands, rctx = self.my_reverse_context(rctx)
        rctx = await self.update_other_children(rctx)
        return rctx

    async def update_other_children(self, rctx):
        for kid in self.children:
            kid._init_widget()  # For current children widget inited from current_child->current_child_idx->widget call.
            if kid is self.current_child:
                continue
            rctx = await kid.update_other_children(rctx)
            kid.view_commands, _unused_rctx = kid.my_reverse_context(rctx)
            if kid.view:
                await kid.view.children_changed(kid.ctx, rctx, kid.widget)
                rctx = kid.view.secondary_parent_context(rctx, kid.widget)
        return rctx

    def my_reverse_context(self, rctx):
        if not self.view:
            return ([], rctx)
        my_rctx = self.view.primary_parent_context(rctx, self.widget)
        command_ctx = self.command_context(my_rctx)
        unbound_view_commands = self._meta.svc.get_view_commands(command_ctx, self.view)
        view_commands = self._bind_commands(unbound_view_commands, command_ctx)
        if self.parent.view:
            parent_command_ctx = self.parent.command_context(my_rctx)
            unbound_element_commands = self._meta.svc.get_view_element_commands(parent_command_ctx, self.parent.view)
            element_command_ctx = parent_command_ctx.clone_with(
                element_idx=self.idx,
                )
            element_commands = self._bind_commands(unbound_element_commands, element_command_ctx)
            view_commands = [*view_commands, *element_commands]
        all_commands = view_commands
        if 'model' in self.ctx.diffs(self.parent.ctx):  # Added or replaced by self.view.children_context.
            model_t = deduce_t(command_ctx.model)
            unbound_model_commands = self._meta.svc.get_ui_model_commands(
                self.ctx.lcs, model_t, command_ctx)
            model_commands = self._bind_commands(unbound_model_commands, command_ctx)
            all_commands = all_commands + model_commands
        commands_rctx = my_rctx.clone_with(
            commands=rctx.get('commands', []) + all_commands,
            )
        return (view_commands, commands_rctx)

    @staticmethod
    def _bind_commands(commands, ctx):
        return [cmd.bind(ctx) for cmd in commands]

    def command_context(self, rctx):
        ctx = self.ctx.clone_with(
            navigator=self.navigator_rec(rctx),
            )
        ctx = ctx.push(
            view=self.view,
            widget=weakref.ref(self.widget),
            hook=self.hook,
            )
        ctx = ctx.copy_from(rctx)
        if 'model' in ctx:
            ctx = ctx.clone_with(
                piece=ctx.model,  # An alias for model.
                )
        if 'model_state' in ctx:
            ctx = ctx.clone_with(**ctx.attributes(ctx.model_state))
        return ctx

    def navigator_rec(self, rctx):
        rctx = self.view.primary_parent_context(rctx, self.widget)
        try:
            return rctx.navigator
        except KeyError:
            pass
        return self.parent.navigator_rec(rctx)

    def update_context(self):
        if not self.view:
            return
        ctx = self.view.children_context(self.ctx)
        for kid in self.children:
            kid.ctx = ctx
            kid.update_context()

    def context_changed_hook(self):
        log.info("Controller: context changed from: %s", self)
        self.update_context()

    def parent_context_changed_hook(self):
        log.info("Controller: parent context changed from: %s", self)
        self.children_changed()

    def current_changed_hook(self):
        log.info("Controller: current changed from: %s", self)
        self._current_child_idx = None
        self.children_changed()
        self.save_state()

    # Should be on stack for proper module for feed constructor be picked up.
    async def _send_model_diff(self, model_diff):
        await self._meta.feed.send(model_diff)

    def _replace_child_item(self, idx):
        view_items = self.view.items()
        item = self._make_child_item(view_items[idx])
        self._children[idx] = item
        self.children_changed()
        self.save_state()
        model_diff = TreeDiff.Replace(self.path, self.model_item)
        asyncio.create_task(self._send_model_diff(model_diff))

    def replace_view_hook(self, new_view, new_state=None):
        log.info("Controller: Replace view @%s -> %s", self, new_view)
        parent = self.parent
        idx = self.idx
        new_widget = new_view.construct_widget(new_state, self.ctx)
        parent.view.replace_child(self.ctx, parent.widget, idx, new_view, new_widget)
        parent._replace_child_item(idx)

    def element_replaced_hook(self, idx, new_view, new_widget):
        log.info("Controller: Element replaced @%s #%d -> %s", self, idx, new_view)
        self._replace_child_item(idx)

    def element_inserted_hook(self, idx):
        view_items = self.view.items()
        item = self._make_child_item(view_items[idx])
        self._children.insert(idx, item)
        self._current_child_idx = None
        self.children_changed()
        self.save_state()
        model_diff = TreeDiff.Insert(item.path, item.model_item)
        asyncio.create_task(self._send_model_diff(model_diff))

    def element_removed_hook(self, idx):
        kid = self._children[idx]
        model_diff = TreeDiff.Remove(kid.path)
        del self._children[idx]
        self._current_child_idx = None
        self.children_changed()
        self.save_state()
        asyncio.create_task(self._send_model_diff(model_diff))

    def elements_changed_hook(self):
        self._children = None
        self._current_child_idx = None
        self.children_changed()
        self.save_state()

    def removed_hook(self):
        self.parent.element_removed_hook(self.idx)

    def replace_parent_widget_hook(self, new_widget):
        parent = self.parent
        parent.view.replace_child_widget(parent.widget, self.idx, new_widget)
        self._widget_wr = None
        self._view_commands = None
        self._model_commands = None

    def save_state_hook(self):
        self.save_state()

    def save_state(self):
        self.parent.save_state()

    @property
    def model_item(self):
        if self.view:
            desc = _description(self.view.piece)
        else:
            desc = '-'
        return htypes.layout.item(self.id, self.name, self.focusable, desc)


@dataclass(repr=False)
class _WindowItem(_Item):

    _window_widget: Any = None

    @classmethod
    def from_refs(cls, meta, ctx, parent, view_ref, state_ref):
        view = meta.svc.view_reg.invite(view_ref, ctx)
        state = web.summon(state_ref)
        item_id = next(meta.counter)
        self = cls(meta, item_id, parent, ctx, f"window#{item_id}", view, focusable=True)
        self._init(state)
        return self

    def _init(self, state):
        widget = self.view.construct_widget(state, self.ctx)
        self._widget_wr = weakref.ref(widget)
        self.view.set_controller_hook(self.hook)
        self._meta.id_to_item[self.id] = self
        self._window_widget = widget  # Prevent windows refs from be gone.

    def children_changed(self):
        asyncio.create_task(self.update_children())

    def save_state(self):
        self.parent.save_state()


@dataclass(repr=False)
class _RootItem(_Item):

    _layout_bundle: Any = None
    _show: bool = True

    @classmethod
    def from_piece(cls, meta, show, ctx, layout_bundle, layout):
        item_id = 0
        self = cls(meta, item_id, None, ctx, "root",
                   view=None, focusable=False, _layout_bundle=layout_bundle, _show=show)
        self.ctx = self.ctx.clone_with(
            root=Root(root_item=self),
            )
        self._children = [
            _WindowItem.from_refs(meta, self.ctx, self, piece_ref, state_ref)
            for piece_ref, state_ref
            in zip(layout.piece.window_list, layout.state.window_list)
            ]
        meta.id_to_item[item_id] = self
        return self

    def show(self):
        for item in self._children:
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

    def children_changed(self):
        pass

    def save_state(self):
        # TODO: Find out real active window.
        # all_windows = QtGui.QGuiApplication.allWindows()
        # current_idx_list = [idx for idx, w in enumerate(all_windows) if w.isActive()]
        # if current_idx_list:
        #     [current_idx] = current_idx_list
        # else:
        current_idx = 0
        layout = htypes.root.layout(
            piece=self._root_piece,
            state=self._root_state(current_idx),
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

    def _root_state(self, current_idx):
        window_list = tuple(
            mosaic.put(item.view.widget_state(item.widget))
            for item in self.children
            )
        return htypes.root.state(window_list, current_idx)

    async def create_window(self, piece, state):
        view = self._meta.svc.view_reg.animate(piece, self.ctx)
        item_id = next(self._meta.counter)
        item = _WindowItem(self._meta, item_id, self, self.ctx, f"window#{item_id}", view, focusable=True)
        item._init(state)
        self._children.append(item)
        await item.update_children()
        if self._show:
            item.widget.show()
        self.save_state()
        model_diff = TreeDiff.Insert(item.path, item.model_item)
        asyncio.create_task(self._send_model_diff(model_diff))

    def navigator_rec(self, rctx):
        return None

    def element_removed_hook(self, idx):
        if len(self.children) > 1:
            super().element_removed_hook(idx)
        else:
            # Last window is closed by user - we are actually exiting now.
            self.save_state()


def _description(piece):
    return str(piece._t)


class Root:

    def __init__(self, root_item):
        self._root_item = root_item

    async def create_window(self, piece, state):
        await self._root_item.create_window(piece, state)


class CtlHook:

    def __init__(self, item):
        self._item = item

    @property
    def canned_item_piece(self):
        return htypes.ui.canned_ctl_item(
            item_id=self._item.id,
            path=tuple(self._item.path),
            )

    def current_changed(self):
        self._item.current_changed_hook()

    def context_changed(self):
        self._item.context_changed_hook()

    def parent_context_changed(self):
        self._item.parent_context_changed_hook()

    def replace_view(self, new_view, new_state=None):
        self._item.replace_view_hook(new_view, new_state)

    def element_inserted(self, idx):
        self._item.element_inserted_hook(idx)

    def element_removed(self, idx):
        self._item.element_removed_hook(idx)

    def removed(self):
        self._item.removed_hook()

    def element_replaced(self, idx, new_view, new_widget=None):
        self._item.element_replaced_hook(idx, new_view, new_widget)

    def elements_changed(self):
        self._item.elements_changed_hook()

    def replace_parent_widget(self, new_widget):
        self._item.replace_parent_widget_hook(new_widget)

    def save_state(self):
        self._item.save_state_hook()


class Controller:

    def __init__(self, svc, layout_bundle, default_layout, ctx, show, load_state):
        self._svc = svc
        self._id_to_item = {}
        self._inside_commands_call = False
        layout = default_layout
        if load_state:
            try:
                layout = layout_bundle.load_piece()
            except FileNotFoundError:
                pass
        meta = ItemMeta(
            svc=svc,
            counter=itertools.count(start=1),
            id_to_item=self._id_to_item,
            feed=svc.feed_factory(htypes.layout.view()),
            )
        root_ctx = ctx.clone_with(controller=self)
        self._root_item = _RootItem.from_piece(meta, show, root_ctx, layout_bundle, layout)

    async def async_init(self):
        for kid in self._root_item.children:
            await kid.update_children()

    def show(self):
        self._root_item.show()

    def pick_canned_item(self, path, item_id):
        item = self._root_item.pick_child(path)
        if not item or item.id != item_id:
            log.warning("View item %s at %s is already gone", item_id, path)
            return None
        return item

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
            if item and item.view_commands:
                return item.view_commands
            else:
                return []
        finally:
            self._inside_commands_call = False


@mark.service
def canned_ctl_item_factory(piece, ctx):
    return ctx.controller.pick_canned_item(piece.path, piece.item_id)


@mark.service
@asynccontextmanager
async def controller_running(
        feed_factory,
        view_reg,
        get_view_commands,
        get_view_element_commands,
        get_ui_model_commands,
        layout_bundle,
        default_layout,
        ctx,
        show=False,
        load_state=False,
        ):
    svc = CtlServices(
        feed_factory=feed_factory,
        view_reg=view_reg,
        get_view_commands=get_view_commands,
        get_view_element_commands=get_view_element_commands,
        get_ui_model_commands=get_ui_model_commands,
        )
    ctl = Controller(svc, layout_bundle, default_layout, ctx, show, load_state)
    await ctl.async_init()
    if show:
        ctl.show()
    yield ctl
