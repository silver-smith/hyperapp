from functools import partial

from .services import (
    ui_command_factory,
    ui_ctl_creg,
    web,
    )
from .code.command_hub import CommandHub


class Controller:

    def __init__(self, root_piece):
        self._root_piece = root_piece
        self._window_list = None

    def create_windows(self, state, ctx):
        self._window_list = [
            self._create_window(web.summon(piece_ref), web.summon(state_ref), ctx)
            for piece_ref, state_ref in zip(self._root_piece.window_list, state.window_list)
            ]

    def _create_window(self, piece, state, ctx):
        view = ui_ctl_creg.animate(piece)
        command_hub = CommandHub()
        window_ctx = ctx.clone_with(command_hub=command_hub)
        widget = view.construct_widget(piece, state, window_ctx)
        wrapper = partial(self._apply_diff_wrapper, window_ctx, command_hub, piece, view, widget)
        commands = self._view_commands(piece, widget, wrappers=[wrapper])
        command_hub.set_commands([], commands)
        widget.show()
        return widget

    def _view_commands(self, piece, widget, wrappers):
        view = ui_ctl_creg.animate(piece)
        commands = ui_command_factory(piece, view, widget, wrappers)
        current = view.get_current(piece, widget)
        if not current:
            return commands
        view_wrapper = partial(view.wrapper, widget)
        current_piece_ref, current_widget = current
        current_piece = web.summon(current_piece_ref)
        current_commands = self._view_commands(current_piece, current_widget, [*wrappers, view_wrapper])
        return [*commands, *current_commands]

    def _apply_diff_wrapper(self, ctx, command_hub, piece, view, widget, diffs):
        layout_diff, state_diff = diffs
        log.info("Apply diffs: %s / %s", layout_diff, state_diff)
        new_piece, new_state = view.apply(ctx, piece, widget, layout_diff, state_diff)
        log.info("Applied piece: %s / %s", new_piece, new_state)
