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


_Window = namedtuple('_Window', 'ctx command_hub piece view widget')


def _name(piece):
    return str(piece._t)


class Controller:

    def __init__(self):
        self._window_list = None
        self._root_piece = None
        self._id_to_children = None
        self._id_to_commands = None
        self._run_callback = True

    def create_windows(self, root_piece, state, ctx, show=True):
        self._root_piece = root_piece
        self._window_list = [
            self._create_window(web.summon(piece_ref), web.summon(state_ref), ctx, show)
            for piece_ref, state_ref in zip(root_piece.window_list, state.window_list)
            ]

    def _create_window(self, piece, state, ctx, show):
        view = ui_ctl_creg.animate(piece)
        command_hub = CommandHub()
        window_ctx = ctx.clone_with(command_hub=command_hub)
        widget = view.construct_widget(piece, state, window_ctx)
        wrapper = partial(self._apply_diff_wrapper, window_ctx, command_hub, piece, view, widget)
        path_to_commands = self._view_commands(command_hub, piece, widget, wrappers=[wrapper], path=[])
        command_hub.set_commands(path_to_commands)
        if show:
            widget.show()
        return _Window(window_ctx, command_hub, piece, view, widget)

    def _view_commands(self, command_hub, piece, widget, wrappers, path):
        view = ui_ctl_creg.animate(piece)
        commands = [
            *ui_command_factory(piece, view, widget, wrappers),
            *view.get_commands(piece, widget, wrappers),
            ]
        view.set_on_state_changed(piece, widget, partial(self._on_state_changed, command_hub, piece, view, widget, wrappers, path))
        path_to_commands = {tuple(path): commands}
        current = view.get_current(piece, widget)
        if not current:
            return path_to_commands
        view.set_on_current_changed(widget, partial(self._on_current_changed, command_hub, piece, view, widget, wrappers, path))
        view_wrapper = partial(view.wrapper, widget)
        idx, current_piece_ref, current_widget = current
        current_piece = web.summon(current_piece_ref)
        current_commands = self._view_commands(command_hub, current_piece, current_widget, [*wrappers, view_wrapper], [*path, idx])
        return {**path_to_commands, **current_commands}

    def _on_current_changed(self, command_hub, piece, view, widget, wrappers, path):
        if not self._run_callback:
            return
        current = view.get_current(piece, widget)
        log.info("Controller: current changed for: (%s) %s/%s -> %s", path, piece, view, current)
        if not current:
            return
        view_wrapper = partial(view.wrapper, widget)
        idx, current_piece_ref, current_widget = current
        current_piece = web.summon(current_piece_ref)
        current_commands = self._view_commands(command_hub, current_piece, current_widget, [*wrappers, view_wrapper], [*path, idx])
        command_hub.set_commands(current_commands)

    def _on_state_changed(self, command_hub, piece, view, widget, wrappers, path):
        if not self._run_callback:
            return
        log.info("Controller: state changed for: (%s) %s/%s", path, piece, view)
        commands = self._view_commands(command_hub, piece, widget, wrappers, path)
        command_hub.set_commands(commands)

    @contextmanager
    def _without_callback(self):
        self._run_callback = False
        try:
            yield
        finally:
            self._run_callback = True

    def _apply_diff_wrapper(self, ctx, command_hub, piece, view, widget, diffs):
        layout_diff, state_diff = diffs
        log.info("Apply diffs: %s / %s", layout_diff, state_diff)
        with self._without_callback():
            result = view.apply(ctx, piece, widget, layout_diff, state_diff)
        if result is None:
            return
        new_piece, new_state, replace = result
        log.info("Applied piece: %s / %s", new_piece, new_state)
        assert not replace  # Not yet supported.
        new_view = ui_ctl_creg.animate(piece)
        wrapper = partial(self._apply_diff_wrapper, ctx, command_hub, new_piece, new_view, widget)
        path_to_commands = self._view_commands(command_hub, new_piece, widget, wrappers=[wrapper], path=[])
        command_hub.set_commands(path_to_commands)

    def view_items(self, item_id):
        if self._id_to_children is None:
            self._populate_view_items()
        return self._id_to_children.get(item_id, [])

    def item_commands(self, item_id):
        return self._id_to_commands.get(item_id, [])

    def _populate_view_items(self):
        counter = itertools.count(start=1)
        self._id_to_children = {}
        self._id_to_commands = {}

        def _populate(item_id, piece, widget, wrappers, path):
            view = ui_ctl_creg.animate(piece)
            commands = self._item_commands(piece, view, widget, wrappers, path)
            self._id_to_commands[item_id] = commands
            children_wrappers = [*wrappers, partial(view.wrapper, widget)]
            items = []
            for idx, rec in enumerate(view.items(piece, widget)):
                item_piece = web.summon(rec.piece_ref)
                child_id = next(counter)
                items.append(htypes.layout.item(child_id, _name(item_piece)))
                _populate(child_id, item_piece, rec.widget, children_wrappers, [*path, idx])
            self._id_to_children[item_id] = items

        items = []
        for window in self._window_list:
            id = next(counter)
            wrapper = partial(
                self._apply_diff_wrapper, window.ctx, window.command_hub, window.piece, window.view, window.widget)
            items.append(htypes.layout.item(id, _name(window.piece)))
            _populate(id, window.piece, window.widget, [wrapper], path=[])
        self._id_to_children[0] = items

    def _item_commands(self, piece, view, widget, wrappers, path):
        return [
            *ui_command_factory(piece, view, widget, wrappers),
            *view.get_commands(piece, widget, wrappers),
            ]


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
