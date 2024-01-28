from .services import (
    ui_ctl_creg,
    web,
    )
from .code.command_hub import CommandHub


class Controller:

    def __init__(self, root_piece):
        self._root_piece = root_piece
        self._window_list = None

    def create_windows(self, state, ctx):
        window_view_list = [
            ui_ctl_creg.invite(piece)
            for piece in self._root_piece.window_list
            ]
        self._window_list = [
            self._create_window(view, web.summon(s), ctx)
            for view, s in zip(window_view_list, state.window_list)
            ]

    def _create_window(self, view, state, ctx):
        command_hub = CommandHub()
        window_ctx = ctx.clone_with(command_hub=command_hub)
        w = view.construct_widget(state, window_ctx)
        w.show()
        return w
