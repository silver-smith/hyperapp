import itertools
import logging
from collections import defaultdict, namedtuple
from contextlib import contextmanager
from functools import partial

from . import htypes
from .services import (
    ui_command_factory,
    ui_ctl_creg,
    web,
    )
from .code.command_hub import CommandHub

log = logging.getLogger(__name__)


_Item = namedtuple('_Item', 'id path ctx command_hub piece view widget wrappers commands children', defaults=([], []))

def _name(piece):
    return str(piece._t)


class Controller:

    def __init__(self):
        self._window_items = None
        self._root_piece = None
        self._id_to_item = None
        self._run_callback = True
        self._counter = itertools.count(start=1)

    def create_windows(self, root_piece, state, ctx, show=True):
        self._root_piece = root_piece
        self._id_to_item = {}
        self._window_items = [
            self._create_window(idx, web.summon(piece_ref), web.summon(state_ref), ctx, show)
            for idx, (piece_ref, state_ref)
            in enumerate(zip(root_piece.window_list, state.window_list))
            ]

    def _create_window(self, idx, piece, state, ctx, show):
        view = ui_ctl_creg.animate(piece)
        command_hub = CommandHub()
        window_ctx = ctx.clone_with(command_hub=command_hub)
        widget = view.construct_widget(piece, state, window_ctx)
        item = self._make_window_item(idx, window_ctx, command_hub, piece, view, widget)
        if show:
            widget.show()
        return item

    # And update window commands.
    def _make_window_item(self, idx, window_ctx, command_hub, piece, view, widget):
        path = [idx]
        wrapper = partial(self._apply_diff_wrapper, idx, window_ctx, command_hub, piece, view, widget)
        item = self._populate_item(path, window_ctx, command_hub, piece, widget, [wrapper])
        path_to_commands = self._collect_item_commands(item)
        command_hub.set_commands(path_to_commands)
        return item

    def _populate_item(self, path, ctx, command_hub, piece, widget, wrappers):
        item_id = next(self._counter)
        view = ui_ctl_creg.animate(piece)
        commands = self._make_item_commands(piece, view, widget, wrappers, path)
        children_wrappers = [*wrappers, partial(view.wrapper, widget)]
        children = []
        for idx, rec in enumerate(view.items(piece, widget)):
            item_piece = web.summon(rec.piece_ref)
            child = self._populate_item(
                [*path, idx], ctx, command_hub, item_piece, rec.widget, children_wrappers)
            children.append(child)
        item = _Item(item_id, path, ctx, command_hub, piece, view, widget, wrappers, commands, children)
        self._id_to_item[item_id] = item
        view.set_on_state_changed(piece, widget, partial(self._on_state_changed, item))
        view.set_on_current_changed(widget, partial(self._on_current_changed, item))
        return item

    def _make_item_commands(self, piece, view, widget, wrappers, path):
        return [
            *ui_command_factory(piece, view, widget, wrappers),
            *view.get_commands(piece, widget, wrappers),
            ]

    def _on_current_changed(self, item):
        if not self._run_callback:
            return
        idx = item.view.get_current(item.piece, item.widget)
        log.info("Controller: current changed for: %s -> %s", item, idx)
        path_to_commands = self._collect_item_commands(item.children[idx])
        item.command_hub.set_commands(path_to_commands)

    def _on_state_changed(self, item):
        if not self._run_callback:
            return
        log.info("Controller: state changed for: %s", item)
        item.commands[:] = self._make_item_commands(item.piece, item.view, item.widget, item.wrappers, item.path)
        path_to_commands = self._collect_item_commands(item)
        item.command_hub.set_commands(path_to_commands)

    def _collect_item_commands(self, item):
        path_to_commands = {tuple(item.path): item.commands}
        if item.children:
            idx = item.view.get_current(item.piece, item.widget)
            path_to_commands.update(self._collect_item_commands(item.children[idx]))
        return path_to_commands
        
    @contextmanager
    def _without_callback(self):
        self._run_callback = False
        try:
            yield
        finally:
            self._run_callback = True

    def _apply_diff_wrapper(self, idx, ctx, command_hub, piece, view, widget, diffs):
        layout_diff, state_diff = diffs
        log.info("Apply diffs: %s / %s", layout_diff, state_diff)
        with self._without_callback():
            result = view.apply(ctx, piece, widget, layout_diff, state_diff)
        if result is None:
            return
        new_piece, new_state, replace = result
        log.info("Applied piece: %s / %s", new_piece, new_state)
        assert not replace  # Not yet supported.
        new_view = ui_ctl_creg.animate(new_piece)
        new_item = self._make_window_item(idx, ctx, command_hub, new_piece, new_view, widget)
        self._window_items[idx] = new_item

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
            htypes.layout.item(item.id, _name(item.piece))
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
    commands = controller.item_commands(current_item.id)
    log.info("Layout tree commands for %s: %s", current_item, commands)
    return commands


async def open_layout_tree():
    return htypes.layout.view()
