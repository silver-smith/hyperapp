from . import htypes
from .services import (
    ui_ctl_creg,
    web,
    )


class AppCtl:

    @classmethod
    def from_piece(cls, layout):
        window_ctl_list = [
            ui_ctl_creg.invite(l)
            for l in layout.window_list
            ]
        return cls(window_ctl_list)

    def __init__(self, window_ctl_list):
        self._window_ctl_list = window_ctl_list

    def construct_widget(self, state, ctx):
        return [
            ctl.construct_widget(web.summon(s), ctx)
            for ctl, s in zip(self._window_ctl_list, state.window_list)
            ]
