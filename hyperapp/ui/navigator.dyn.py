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
        return self._current_view.construct_widget(state, ctx)

    def get_current(self, widget):
        return 0

    @property
    def is_navigator(self):
        return True

    def widget_state(self, widget):
        return self._current_view.widget_state(widget)

    def _replace_widget(self, ctx, state):
        new_widget = self.construct_widget(state, ctx)
        self._ctl_hook.replace_parent_widget(new_widget)
        self._ctl_hook.element_replaced(0, self._current_view, new_widget)

    def _history_rec(self, widget):
        model_t = deduce_t(self._model)
        return htypes.navigator.history_rec(
            view=mosaic.put(self._current_view.piece),
            model=mosaic.put(self._model, model_t),
            state=mosaic.put(self.widget_state(widget)),
            prev=self._prev,
            next=self._next,
            )

    def open(self, ctx, model, view, widget):
        history_rec = self._history_rec(widget)
        self._current_view = view
        self._model = model
        self._prev = mosaic.put(history_rec)
        self._next = None
        state = None  # TODO: Devise new state.
        self._replace_widget(ctx, state)

    def go_back(self, ctx, widget):
        if not self._prev:
            return
        history_rec = self._history_rec(widget)
        prev = web.summon(self._prev)
        prev_model = web.summon(prev.model)
        prev_state = web.summon(prev.state)
        self._current_view = model_view_creg.invite(prev.view, prev_model, ctx)
        self._model = web.summon(prev.model)
        self._prev = prev.prev
        self._next = mosaic.put(history_rec)
        self._replace_widget(ctx, prev_state)

    def go_forward(self, ctx, widget):
        if not self._next:
            return
        history_rec = self._history_rec(widget)
        next = web.summon(self._next)
        next_model = web.summon(next.model)
        next_state = web.summon(next.state)
        self._current_view = model_view_creg.invite(next.view, next_model, ctx)
        self._model = web.summon(next.model)
        self._prev = mosaic.put(history_rec)
        self._next = next.next
        self._replace_widget(ctx, next_state)

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
def go_back(view, widget, ctx):
    view.go_back(ctx, widget)


@mark.ui_command(htypes.navigator.view)
def go_forward(view, widget, ctx):
    view.go_forward(ctx, widget)
