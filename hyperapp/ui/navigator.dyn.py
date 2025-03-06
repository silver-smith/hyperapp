import logging
import weakref
from collections import namedtuple

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.view import Item, View

log = logging.getLogger(__name__)


_NavigatorRec = namedtuple('_NavigatorRec', 'view state widget_wr hook')


class NavigatorView(View):

    @classmethod
    @mark.view
    def from_piece(cls, piece, ctx, view_reg, model_layout_reg):
        model = web.summon(piece.current_model)
        model_ctx = ctx.clone_with(model=model)
        layout_k = web.summon_opt(piece.layout_k)
        current_view = view_reg.invite(piece.current_view, model_ctx)
        return cls(model_layout_reg, current_view, model, layout_k, piece.prev, piece.next)

    def __init__(self, model_layout_reg, current_view, model, layout_k, prev, next):
        super().__init__()
        self._model_layout_reg = model_layout_reg
        self._current_view = current_view
        self._current_layout = current_view.piece
        self._model = model  # piece
        self._layout_k = layout_k  # Key for model_layout_reg.
        self._prev = prev  # ref opt
        self._next = next  # ref opt

    @property
    def piece(self):
        model_t = deduce_t(self._model)
        return htypes.navigator.view(
            current_view=mosaic.put(self._current_view.piece),
            current_model=mosaic.put(self._model, model_t),
            layout_k=mosaic.put_opt(self._layout_k),
            prev=self._prev,
            next=self._next,
            )
            
    def construct_widget(self, state, ctx):
        return self._current_view.construct_widget(state, ctx)

    def get_current(self, widget):
        return 0

    def children_context(self, ctx):
        return ctx.clone_with(model=self._model)

    def primary_parent_context(self, rctx, widget):
        state = self.widget_state(widget)
        return rctx.clone_with(
            navigator=_NavigatorRec(self, state, weakref.ref(widget), self._ctl_hook),
            current_model=self._model,
            )

    def widget_state(self, widget):
        return self._current_view.widget_state(widget)

    def _replace_widget(self, ctx, state):
        new_widget = self.construct_widget(state, ctx)
        self._ctl_hook.replace_parent_widget(new_widget)
        self._ctl_hook.context_changed()
        self._ctl_hook.element_replaced(0, self._current_view, new_widget)

    def _history_rec(self, widget):
        model_t = deduce_t(self._model)
        return htypes.navigator.history_rec(
            view=mosaic.put(self._current_view.piece),
            model=mosaic.put(self._model, model_t),
            state=mosaic.put(self.widget_state(widget)),
            layout_k=mosaic.put_opt(self._layout_k),
            prev=self._prev,
            next=self._next,
            )

    def open(self, ctx, model, view, widget, layout_k=None):
        history_rec = self._history_rec(widget)
        self._current_view = view
        self._current_layout = view.piece
        self._model = model
        self._layout_k = layout_k
        self._prev = mosaic.put(history_rec)
        self._next = None
        state = None  # TODO: Devise new state.
        self._replace_widget(ctx, state)

    def go_back(self, ctx, widget, view_reg):
        if not self._prev:
            return
        history_rec = self._history_rec(widget)
        prev = web.summon(self._prev)
        prev_model = web.summon(prev.model)
        prev_state = web.summon(prev.state)
        model_ctx = ctx.pop().clone_with(model=prev_model)
        self._current_view = view_reg.invite(prev.view, model_ctx)
        self._current_layout = self._current_view.piece
        self._model = web.summon(prev.model)
        self._layout_k = web.summon_opt(prev.layout_k)
        self._prev = prev.prev
        self._next = mosaic.put(history_rec)
        self._replace_widget(ctx, prev_state)

    def go_forward(self, ctx, widget, view_reg):
        if not self._next:
            return
        history_rec = self._history_rec(widget)
        next = web.summon(self._next)
        next_model = web.summon(next.model)
        next_state = web.summon(next.state)
        model_ctx = ctx.pop().clone_with(model=next_model)
        self._current_view = view_reg.invite(next.view, model_ctx)
        self._current_layout = self._current_view.piece
        self._model = web.summon(next.model)
        self._layout_k = web.summon_opt(next.layout_k)
        self._prev = mosaic.put(history_rec)
        self._next = next.next
        self._replace_widget(ctx, next_state)

    def _set_layout(self, layout):
        model_t = deduce_t(self._model)
        if self._layout_k is not None:
            layout_k = self._layout_k
        else:
            layout_k = htypes.ui.model_layout_k(
                model_t=pyobj_creg.actor_to_ref(model_t),
                )
        self._model_layout_reg[layout_k] = layout
        self._current_layout = self._current_view.piece

    def replace_child(self, ctx, widget, idx, new_child_view, new_child_widget):
        assert idx == 0
        self._current_view = new_child_view
        self._ctl_hook.replace_parent_widget(new_child_widget)
        self._set_layout(new_child_view.piece)

    async def children_changed(self, ctx, rctx, widget):
        layout = self._current_view.piece
        if layout != self._current_layout:
            log.info("Navigator: children layout changed: %s", layout)
            self._set_layout(layout)

    def items(self):
        return [Item('current', self._current_view)]

    def item_widget(self, widget, idx):
        if idx == 0:
            return widget
        return super().item_widget(widget, idx)


@mark.ui_command(htypes.navigator.view)
def go_back(view, widget, ctx, view_reg):
    view.go_back(ctx, widget, view_reg)


@mark.ui_command(htypes.navigator.view)
def go_forward(view, widget, ctx, view_reg):
    view.go_forward(ctx, widget, view_reg)
