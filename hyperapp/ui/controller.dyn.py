from .services import (
    ui_ctl_creg,
    web,
    )


class Controller:

    def __init__(self, root_piece):
        self._root_piece = root_piece

    def create_windows(self, state, ctx):
        window_view_list = [
            ui_ctl_creg.invite(piece)
            for piece in self._root_piece.window_list
            ]
        return [
            self._create_window(view, web.summon(s), ctx)
            for view, s in zip(window_view_list, state.window_list)
            ]

    def _create_window(self, view, state, ctx):
        w = view.construct_widget(state, ctx)
        w.show()
