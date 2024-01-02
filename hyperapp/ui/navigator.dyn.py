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
        fn = self._fn
        if isinstance(fn, partial):
            fn = fn.func
        return fn.__name__

    async def run(self):
        log.info("Run: %s", self._fn)
        result = await self._fn()
        log.info("Run result: %s -> %r", self._fn, result)
        return self._wrapper(result)


async def open_sample_text_1():
    return "Sample text 1"


async def open_sample_text_2():
    return "Sample text 2"


async def open_sample_list():
    return [
        htypes.sample_list.item(1, "First"),
        htypes.sample_list.item(2, "Second"),
        htypes.sample_list.item(3, "Third"),
        ]


class NavigatorCtl:

    @classmethod
    def from_piece(cls, layout):
        current_ctl = ui_ctl_creg.invite(layout.current_layout)
        return cls(current_ctl)

    def __init__(self, current_ctl):
        self._current_ctl = current_ctl

    def construct_widget(self, state, ctx):
        if state is not None:
            current_state = web.summon(state.current_state)
        else:
            current_state = None
        return self._current_ctl.construct_widget(current_state, ctx)

    def widget_state(self, widget):
        current_state = self._current_ctl.widget_state(widget)
        return htypes.navigator.state(
            current_state=mosaic.put(current_state),
            prev=None,
            next=None,
            )

    def get_commands(self, layout, widget, wrapper):
        sample_command_1 = ModelCommand(open_sample_text_1, partial(self._wrapper, layout, wrapper))
        sample_command_2 = ModelCommand(open_sample_text_2, partial(self._wrapper, layout, wrapper))
        sample_command_3 = ModelCommand(open_sample_list, partial(self._wrapper, layout, wrapper))
        commands = [sample_command_1, sample_command_2, sample_command_3]
        if layout.prev:
            commands.append(ModelCommand(self._go_back, wrapper))
        if layout.next:
            commands.append(ModelCommand(self._go_forward, wrapper))
        return commands

    def _wrapper(self, layout, wrapper, piece):
        if piece is None:
            return None
        current_layout = visualizer(piece)
        layout_diff = htypes.navigator.open_new_diff(
            new_current=mosaic.put(current_layout),
            )
        return wrapper((layout_diff, None))

    async def _go_back(self):
        layout_diff = htypes.navigator.go_back_diff()
        return (layout_diff, None)

    async def _go_forward(self):
        layout_diff = htypes.navigator.go_forward_diff()
        return (layout_diff, None)

    def apply(self, ctx, layout, widget, layout_diff, state_diff):
        log.info("Navigator: apply: %s / %s", layout_diff, state_diff)
        if isinstance(layout_diff, htypes.navigator.open_new_diff):
            layout = htypes.navigator.layout(
                current_layout=layout_diff.new_current,
                prev=mosaic.put(layout),
                next=None,
                )
            return (layout, None)
        if isinstance(layout_diff, htypes.navigator.go_back_diff):
            prev_layout = web.summon(layout.prev)
            layout = htypes.navigator.layout(
                current_layout=prev_layout.current_layout,
                prev=prev_layout.prev,
                next=mosaic.put(layout),
                )
            return (layout, None)
        if isinstance(layout_diff, htypes.navigator.go_forward_diff):
            next_layout = web.summon(layout.next)
            layout = htypes.navigator.layout(
                current_layout=next_layout.current_layout,
                prev=mosaic.put(layout),
                next=next_layout.next,
                )
            return (layout, None)
        raise NotImplementedError(repr(layout_diff))
