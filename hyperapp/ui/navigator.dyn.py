import logging
from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from . import htypes
from .services import (
    mark,
    model_command_creg,
    mosaic,
    types,
    ui_ctl_creg,
    visualizer,
    web,
    )
from .code.model_command import global_commands, model_commands, enum_model_commands
from .code.view import View

log = logging.getLogger(__name__)


class NavigatorView(View):

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
        return (0, piece.current_layout, widget)

    def widget_state(self, piece, widget):
        current_piece = web.summon(piece.current_layout)
        current_view = ui_ctl_creg.animate(current_piece)
        current_state = current_view.widget_state(current_piece, widget)
        return htypes.navigator.state(
            current_state=mosaic.put(current_state),
            prev=None,
            next=None,
            )

    def get_commands(self, piece, widget, wrappers):
        model_piece = web.summon(piece.current_model)
        current_view = ui_ctl_creg.invite(piece.current_layout)
        commands = [
            model_command_creg.invite(
                cmd, current_view, model_piece, widget, [*wrappers, self._model_wrapper])
            for cmd in piece.commands
            ]
        state = current_view.model_state(widget)
        return [
            *commands,
            *enum_model_commands(model_piece, state),
            ]

    def _model_wrapper(self, piece):
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
            commands=[mosaic.put(cmd) for cmd in commands],
            )
        return (layout_diff, None)

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
            if not layout.prev:
                return None
            prev_layout = web.summon(layout.prev)
            layout = htypes.navigator.layout(
                current_layout=prev_layout.current_layout,
                current_model=prev_layout.current_model,
                commands=prev_layout.commands,
                prev=prev_layout.prev,
                next=mosaic.put(layout),
                )
        elif isinstance(layout_diff, htypes.navigator.go_forward_diff):
            if not layout.next:
                return None
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
        return (layout, None, True)


@mark.ui_command(htypes.navigator.layout)
def go_back(layout, state):
    layout_diff = htypes.navigator.go_back_diff()
    return (layout_diff, None)

@mark.ui_command(htypes.navigator.layout)
def go_forward(layout, state):
    layout_diff = htypes.navigator.go_forward_diff()
    return (layout_diff, None)
