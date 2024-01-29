import logging
from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from . import htypes
from .services import (
    model_command_creg,
    mosaic,
    types,
    ui_ctl_creg,
    visualizer,
    web,
    )
from .code.model_command import global_commands, model_commands

log = logging.getLogger(__name__)


class _UiCommand:

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


class NavigatorCtl:

    @classmethod
    def from_piece(cls, layout):
        return cls()

    def construct_widget(self, piece, state, ctx):
        current_piece = web.summon(piece.current_layout)
        current_view = ui_ctl_creg.animate(current_piece)
        if state is not None:
            current_state = web.summon(state.current_state)
        else:
            current_state = None
        return current_view.construct_widget(current_piece, current_state, ctx)

    def get_current(self, piece, widget):
        return None

    def widget_state(self, piece, widget):
        current_piece = web.summon(piece.current_layout)
        current_view = ui_ctl_creg.animate(current_piece)
        current_state = current_view.widget_state(current_piece, widget)
        return htypes.navigator.state(
            current_state=mosaic.put(current_state),
            prev=None,
            next=None,
            )

    def get_commands(self, layout, widget, wrapper):
        model_wrapper = partial(self._wrapper, layout, wrapper)
        model_piece = web.summon(layout.current_model)
        commands = [
            model_command_creg.invite(cmd, self._current_ctl, model_piece, widget, model_wrapper)
            for cmd in layout.commands
            ]
        if layout.prev:
            commands.append(_UiCommand(self._go_back, wrapper))
        if layout.next:
            commands.append(_UiCommand(self._go_forward, wrapper))
        return commands

    def _wrapper(self, layout, wrapper, piece):
        if piece is None:
            return None
        new_current_layout = visualizer(piece)
        commands = [
            *global_commands(),
            *model_commands(piece),
            ]
        piece_t = deduce_complex_value_type(mosaic, types, piece)
        layout_diff = htypes.navigator.open_new_diff(
            new_current=mosaic.put(new_current_layout),
            new_model=mosaic.put(piece, piece_t),
            commands=[mosaic.put(c) for c in commands],
            )
        return wrapper((layout_diff, None))

    def apply(self, ctx, layout, widget, layout_diff, state_diff):
        log.info("Navigator: apply: %s / %s", layout_diff, state_diff)
        if isinstance(layout_diff, htypes.navigator.open_new_diff):
            layout = htypes.navigator.layout(
                current_layout=layout_diff.new_current,
                current_model=layout_diff.new_model,
                commands=layout_diff.commands,
                prev=mosaic.put(layout),
                next=None,
                )
        elif isinstance(layout_diff, htypes.navigator.go_back_diff):
            prev_layout = web.summon(layout.prev)
            layout = htypes.navigator.layout(
                current_layout=prev_layout.current_layout,
                current_model=prev_layout.current_model,
                commands=prev_layout.commands,
                prev=prev_layout.prev,
                next=mosaic.put(layout),
                )
        elif isinstance(layout_diff, htypes.navigator.go_forward_diff):
            next_layout = web.summon(layout.next)
            layout = htypes.navigator.layout(
                current_layout=next_layout.current_layout,
                current_model=next_layout.current_model,
                commands=next_layout.commands,
                prev=mosaic.put(layout),
                next=next_layout.next,
                )
        else:
            raise NotImplementedError(repr(layout_diff))
        self._current_ctl = ui_ctl_creg.invite(layout.current_layout)
        return (layout, None)


async def go_back(layout, state):
    layout_diff = htypes.navigator.go_back_diff()
    return (layout_diff, None)

async def go_forward(layout, state):
    layout_diff = htypes.navigator.go_forward_diff()
    return (layout_diff, None)
