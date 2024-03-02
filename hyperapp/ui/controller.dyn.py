import itertools
import logging
from collections import defaultdict, namedtuple
from contextlib import contextmanager
from functools import partial

from . import htypes
from .services import (
    mosaic,
    ui_command_factory,
    ui_ctl_creg,
    web,
    )
from .code.list_diff import ListDiff
from .code.view import View
from .code.command_hub import CommandHub

log = logging.getLogger(__name__)


_Item = namedtuple('_Item', 'id path ctx command_hub name view widget commands children', defaults=([], []))


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


class Controller:

    def __init__(self):
        self._window_items = None
        self._root_ctx = None
        self._id_to_item = None
        self._id_to_parent_item = None
        self._run_callback = True
        self._counter = itertools.count(start=1)

    def create_windows(self, root_piece, state, ctx, show=True):
        self._root_ctx = ctx
        self._id_to_item = {}
        self._id_to_parent_item = {}
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
        return self._populate_item(item_id, path, window_ctx, command_hub, f"window#{item_id}", view, widget)

    def _populate_item(self, item_id, path, ctx, command_hub, name, view, widget):
        commands = self._make_item_commands(item_id, view, widget)
        children = []
        for idx, rec in enumerate(view.items(widget)):
            child_id = next(self._counter)
            child = self._populate_item(
                child_id, [*path, idx], ctx, command_hub, rec.name, rec.view, rec.widget)
            children.append(child)
        item = _Item(item_id, path, ctx, command_hub, name, view, widget, commands, children)
        for child in item.children:
            self._id_to_parent_item[child.id] = item
        self._id_to_item[item_id] = item
        view.set_on_item_changed(partial(self._on_item_changed, item))
        view.set_on_child_changed(partial(self._on_child_changed, item))
        view.set_on_current_changed(widget, partial(self._on_current_changed, item))
        view.set_on_state_changed(widget, partial(self._on_state_changed, item))
        return item

    def _make_item_commands(self, item_id, view, widget):
        wrapper = partial(self._apply_item_diff, item_id)
        return self._make_view_commands(view, widget, wrapper)

    def _make_view_commands(self, view, widget, wrapper):
        return [
            *ui_command_factory(view, widget, [wrapper]),
            *view.get_commands(widget, [wrapper]),
            ]

    def _on_item_changed(self, item):
        log.info("Item is changed: %s", item)
        parent = self._id_to_parent_item[item.id]
        idx = parent.children.index(item)
        self._replace_child_item(parent, idx, item.widget)

    def _on_child_changed(self, item, idx, widget):
        log.info("Child #%d changed for: %s", idx, item)
        self._replace_child_item(item, idx, widget)

    def _replace_child_item(self, item, idx, widget):
        old_child = item.children[idx]
        child_id = next(self._counter)
        child = self._populate_item(
            child_id, old_child.path, old_child.ctx, old_child.command_hub, old_child.name, old_child.view, widget)
        self._id_to_parent_item[child.id] = item
        item.children[idx] = child
        self._update_item_commands(child)

    def _update_item_commands(self, item):
        path_to_commands = self._collect_item_commands(item)
        item.command_hub.set_commands(path_to_commands)

    def _on_current_changed(self, item):
        if not self._run_callback:
            return
        idx = item.view.get_current(item.widget)
        log.info("Controller: current changed to #%d for: %s", idx, item)
        self._update_item_commands(item.children[idx])

    def _on_state_changed(self, item):
        if not self._run_callback:
            return
        log.info("Controller: state changed for: %s", item)
        item.commands[:] = self._make_item_commands(item.id, item.view, item.widget)
        self._update_item_commands(item)

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

    def _apply_item_diff(self, item_id, diff):
        if diff is None:
            return
        item = self._id_to_item[item_id]
        log.info("Apply diff to item #%d @ %s: %s", item_id, item.path, diff)
        with self._without_callback():
            replace_widget = item.view.apply(item.ctx, item.widget, diff)
            log.info("Applied diff, should replace widget: %s", replace_widget)
            if not replace_widget:
                return
            parent = self._id_to_parent_item[item_id]
            parent.view.replace_widget(parent.ctx, parent.widget, item.path[-1])

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
            htypes.layout.item(item.id, item.name, _description(item.view.piece))
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


async def open_layout_item_commands(piece, current_item):
    log.info("Open layout item commands for: %s", current_item)
    if current_item:
        return htypes.layout.command_list(item_id=current_item.id)


def layout_item_commands(piece):
    command_list = [
        htypes.layout.command_item(command.name)
        for command in controller.item_commands(piece.item_id)
        ]
    log.info("Get layout item commands for %s: %s", piece, command_list)
    return command_list


async def add_layout_command(piece, current_item):
    log.info("Add layout command for %s: %s", piece, current_item)
