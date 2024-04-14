import logging
from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from . import htypes
from .services import (
    mark,
    model_command_creg,
    mosaic,
    types,
    view_creg,
    visualizer,
    web,
    )
from .code.model_command import global_commands, model_commands, enum_model_commands
from .code.view import Diff, Item, View

log = logging.getLogger(__name__)


class NavigatorView(View):

    @classmethod
    def from_piece(cls, piece, ctx):
        current_view = view_creg.invite(piece.current_view, ctx)
        current_model = web.summon(piece.current_model)
        return cls(current_view, current_model, piece.commands, piece.prev, piece.next)

    def __init__(self, current_view, current_model, commands, prev, next):
        super().__init__()
        self._current_view = current_view
        self._current_model = current_model  # piece
        self._commands = commands  # ref list
        self._prev = prev  # ref opt
        self._next = next  # ref opt

    @property
    def piece(self):
        model_t = deduce_complex_value_type(mosaic, types, self._current_model)
        return htypes.navigator.view(
            current_view=mosaic.put(self._current_view.piece),
            current_model=mosaic.put(self._current_model, model_t),
            commands=self._commands,
            prev=self._prev,
            next=self._next,
            )
            
    def construct_widget(self, state, ctx):
        if state is not None:
            current_state = web.summon(state.current_state)
        else:
            current_state = None
        return self._current_view.construct_widget(current_state, ctx)

    def get_current(self, widget):
        return 0

    def get_model(self):
        return self._current_model

    async def child_state_changed(self, ctx, widget):
        self._ctl_hook.commands_changed()

    def widget_state(self, widget):
        current_state = self._current_view.widget_state(widget)
        return htypes.navigator.state(
            current_state=mosaic.put(current_state),
            prev=None,
            next=None,
            )

    def get_commands(self, widget, wrappers):
        commands = [
            model_command_creg.invite(
                cmd, self._current_view, self._current_model, widget, [*wrappers, self._model_wrapper])
            for cmd in self._commands
            ]
        state = self._current_view.model_state(widget)
        return [
            *commands,
            *enum_model_commands(self._current_model, state),
            ]

    def _model_wrapper(self, piece):
        if piece is None:
            return None
        if type(piece) is list:
            piece = tuple(piece)
        new_current_view = visualizer(piece)
        commands = [
            *global_commands(),
            *model_commands(piece),
            ]
        piece_t = deduce_complex_value_type(mosaic, types, piece)
        return Diff(htypes.navigator.open_new_diff(
            new_current=mosaic.put(new_current_view),
            new_model=mosaic.put(piece, piece_t),
            commands=tuple(mosaic.put(cmd) for cmd in commands),
            ))

    def apply(self, ctx, widget, diff):
        log.info("Navigator: apply: %s", diff)
        if isinstance(diff.piece, htypes.navigator.open_new_diff):
            current_piece = self.piece
            self._current_view = view_creg.invite(diff.piece.new_current, ctx)
            self._current_model = web.summon(diff.piece.new_model)
            self._commands = diff.piece.commands
            self._prev = mosaic.put(current_piece)
            self._next = None
        elif isinstance(diff.piece, htypes.navigator.go_back_diff):
            if not self._prev:
                return None
            current_piece = self.piece
            prev = web.summon(self._prev)
            self._current_view = view_creg.invite(prev.current_view, ctx)
            self._current_model = web.summon(prev.current_model)
            self._commands = prev.commands
            self._prev = prev.prev
            self._next = mosaic.put(current_piece)
        elif isinstance(diff.piece, htypes.navigator.go_forward_diff):
            if not self._next:
                return None
            current_piece = self.piece
            next = web.summon(self._next)
            self._current_view = view_creg.invite(next.current_view, ctx)
            self._current_model = web.summon(next.current_model)
            self._commands = next.commands
            self._prev = mosaic.put(current_piece)
            self._next = next.next
        else:
            raise NotImplementedError(repr(diff.piece))
        state = None  # TODO: Devise new state.
        new_widget = self.construct_widget(state, ctx)
        self._ctl_hook.replace_item_element(0, self._current_view, new_widget)
        self._ctl_hook.replace_parent_widget(new_widget)

    def replace_child(self, widget, idx, new_child_view, new_child_widget):
        assert idx == 0
        self._current_view = new_child_view
        # self._commands = []  # TODO
        self._ctl_hook.replace_parent_widget(new_child_widget)

    def items(self):
        return [Item('current', self._current_view)]

    def item_widget(self, widget, idx):
        if idx == 0:
            return widget
        return super().item_widget(widget, idx)


@mark.ui_command(htypes.navigator.view)
def go_back(piece, state):
    return Diff(htypes.navigator.go_back_diff())


@mark.ui_command(htypes.navigator.view)
def go_forward(piece, state):
    return Diff(htypes.navigator.go_forward_diff())
