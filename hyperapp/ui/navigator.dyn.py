import logging
from functools import partial

from . import htypes
from .services import (
    deduce_t,
    mark,
    mosaic,
    model_view_creg,
    web,
    )

from .code.view import Item, View

log = logging.getLogger(__name__)


class NavigatorView(View):

    @classmethod
    def from_piece(cls, piece, ctx):
        model = web.summon(piece.current_model)
        current_view = model_view_creg.invite(piece.current_view, model, ctx)
        return cls(current_view, model, piece.prev, piece.next)

    def __init__(self, current_view, model, prev, next):
        super().__init__()
        self._current_view = current_view
        self._model = model  # piece
        self._prev = prev  # ref opt
        self._next = next  # ref opt

    @property
    def piece(self):
        model_t = deduce_t(self._model)
        return htypes.navigator.view(
            current_view=mosaic.put(self._current_view.piece),
            current_model=mosaic.put(self._model, model_t),
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

    @property
    def is_navigator(self):
        return True

    def widget_state(self, widget):
        current_state = self._current_view.widget_state(widget)
        return htypes.navigator.state(
            current_state=mosaic.put(current_state),
            prev=None,
            next=None,
            )

    def _replace_widget(self, ctx):
        state = None  # TODO: Devise new state.
        new_widget = self.construct_widget(state, ctx)
        self._ctl_hook.replace_parent_widget(new_widget)
        self._ctl_hook.element_replaced(0, self._current_view, new_widget)

    def open(self, ctx, model, view):
        current_piece = self.piece
        self._current_view = view
        self._model = model
        self._prev = mosaic.put(current_piece)
        self._next = None
        self._replace_widget(ctx)

    def go_back(self, ctx):
        if not self._prev:
            return
        current_piece = self.piece
        prev = web.summon(self._prev)
        prev_model = web.summon(prev.current_model)
        self._current_view = model_view_creg.invite(prev.current_view, prev_model, ctx)
        self._model = web.summon(prev.current_model)
        self._prev = prev.prev
        self._next = mosaic.put(current_piece)
        self._replace_widget(ctx)

    def go_forward(self, ctx):
        if not self._next:
            return
        current_piece = self.piece
        next = web.summon(self._next)
        next_model = web.summon(next.current_model)
        self._current_view = model_view_creg.invite(next.current_view, next_model, ctx)
        self._model = web.summon(next.current_model)
        self._prev = mosaic.put(current_piece)
        self._next = next.next
        self._replace_widget(ctx)

    def replace_child(self, widget, idx, new_child_view, new_child_widget):
        assert idx == 0
        self._current_view = new_child_view
        self._ctl_hook.replace_parent_widget(new_child_widget)

    def items(self):
        return [Item('current', self._current_view)]

    def item_widget(self, widget, idx):
        if idx == 0:
            return widget
        return super().item_widget(widget, idx)


@mark.ui_command(htypes.navigator.view)
def go_back(view, ctx):
    view.go_back(ctx)


@mark.ui_command(htypes.navigator.view)
def go_forward(view, ctx):
    view.go_forward(ctx)
