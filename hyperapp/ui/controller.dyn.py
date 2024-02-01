import itertools
import logging
from collections import defaultdict
from functools import partial

from . import htypes
from .services import (
    ui_command_factory,
    ui_ctl_creg,
    web,
    )
from .code.command_hub import CommandHub

log = logging.getLogger(__name__)


def _name(piece):
    return str(piece._t)


class Controller:

    def __init__(self):
        self._window_list = None
        self._root_piece = None
        self._parent_id_to_items = None

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
        commands = self._view_commands(piece, widget, wrappers=[wrapper])
        command_hub.set_commands([], commands)
        if show:
            widget.show()
        return widget

    def _view_commands(self, piece, widget, wrappers):
        view = ui_ctl_creg.animate(piece)
        commands = ui_command_factory(piece, view, widget, wrappers)
        if hasattr(view, 'get_commands'):
            commands += view.get_commands(piece, widget, wrappers)
        current = view.get_current(piece, widget)
        if not current:
            return commands
        view_wrapper = partial(view.wrapper, widget)
        current_piece_ref, current_widget = current
        current_piece = web.summon(current_piece_ref)
        current_commands = self._view_commands(current_piece, current_widget, [*wrappers, view_wrapper])
        return commands + current_commands

    def _apply_diff_wrapper(self, ctx, command_hub, piece, view, widget, diffs):
        layout_diff, state_diff = diffs
        log.info("Apply diffs: %s / %s", layout_diff, state_diff)
        new_piece, new_state, replace = view.apply(ctx, piece, widget, layout_diff, state_diff)
        log.info("Applied piece: %s / %s", new_piece, new_state)
        assert not replace  # Not yet supported.
        new_view = ui_ctl_creg.animate(piece)
        wrapper = partial(self._apply_diff_wrapper, ctx, command_hub, new_piece, new_view, widget)
        commands = self._view_commands(new_piece, widget, wrappers=[wrapper])
        command_hub.set_commands([], commands)

    def view_items(self, parent_id):
        if self._parent_id_to_items is None:
            self._populate_view_items()
        return self._parent_id_to_items[parent_id]

    def _populate_view_items(self):
        counter = itertools.count(start=1)
        self._parent_id_to_items = defaultdict(list)
        items = []
        for window_ref in self._root_piece.window_list:
            window_piece = web.summon(window_ref)
            id = next(counter)
            items.append(htypes.layout.item(id, _name(window_piece)))
        self._parent_id_to_items[0] = items


controller = Controller()


def layout_tree(piece, parent):
    if parent is None:
        parent_id = 0
    else:
        parent_id = parent.id
    return controller.view_items(parent_id)


async def open_layout_tree():
    return htypes.layout.view()
