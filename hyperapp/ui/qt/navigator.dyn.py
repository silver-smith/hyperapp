import logging
from functools import partial

from . import htypes
from .services import (
    mosaic,
    ui_ctl_creg,
    visualizer,
    web,
    )

log = logging.getLogger(__name__)


class ModelCommand:

    def __init__(self, fn, wrapper):
        self._fn = fn
        self._wrapper = wrapper

    @property
    def name(self):
        return self._fn.__name__

    async def run(self):
        log.info("Run: %s", self._fn)
        result = await self._fn()
        log.info("Run result: %s -> %r", self._fn, result)
        return self._wrapper(result)


async def open_some_text():
    return "Some text"


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
        command = ModelCommand(open_some_text, partial(self._wrapper, wrapper))
        return [command]

    def _wrapper(self, wrapper, piece):
        if piece is None:
            return None
        layout = visualizer(piece)
        # Navigator does not have specific diffs. It's diff is just a new layout.
        return wrapper((layout, None))

    def apply(self, ctx, widget, layout_diff, state_diff):
        log.info("Navigator: apply: %s / %s", layout_diff, state_diff)
        return (layout_diff, state_diff)
