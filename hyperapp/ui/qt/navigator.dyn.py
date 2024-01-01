from . import htypes
from .services import (
    mosaic,
    ui_ctl_creg,
    web,
    )


class NavigatorCtl:

    @classmethod
    def from_piece(cls, layout):
        current_ctl = ui_ctl_creg.invite(layout.current_layout)
        return cls(current_ctl)

    def __init__(self, current_ctl):
        self._current_ctl = current_ctl

    def construct_widget(self, state, ctx):
        current_state = web.summon(state.current_state)
        return self._current_ctl.construct_widget(current_state, ctx)

    def widget_state(self, widget):
        current_state = self._current_ctl.widget_state(widget)
        return htypes.navigator.state(mosaic.put(current_state))

    def get_commands(self, layout, widget, wrapper):
        return []

    def apply(self, ctx, widget, layout_diff, state_diff):
        log.info("Navigator: apply: %s / %s", layout_diff, state_diff)
