import logging

from hyperapp.boot.htypes import TRecord

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    web,
    )
from .code.mark import mark
from .code.context_view import ContextView

log = logging.getLogger(__name__)


model_mark_prefix = 'mark-'


def model_mark_name(model_t):
    return f'{model_mark_prefix}{model_t.full_name}'


def value_mark_name(value_t):
    return f'arg-value-{value_t.full_name}'


class MarkView(ContextView):

    @classmethod
    @mark.view
    def from_piece(cls, piece, ctx, format, view_reg):
        base_view = view_reg.invite(piece.base, ctx)
        model, model_t = web.summon_with_t(piece.model)
        value, value_t = web.summon_with_t_opt(piece.value)
        mark_label = format(model)
        items = {}
        items[model_mark_name(model_t)] = model
        if value is not None:
            items[value_mark_name(value_t)] = value
            mark_label += ", " + format(value)
        return cls(base_view, model, value, items, mark_label)

    def __init__(self, base_view, model, value, items, mark_label):
        super().__init__(base_view, label=f"Mark: {mark_label}")
        self._model = model
        self._value = value
        self._items = items

    @property
    def piece(self):
        return htypes.arg_mark.view(
            base=mosaic.put(self._base_view.piece),
            model=mosaic.put(self._model),
            value=mosaic.put_opt(self._value),
            )

    def children_context(self, ctx):
        return ctx.clone_with(self._items)


@mark.ui_command
def add_mark(view, state, hook, current_model, ctx, view_reg, selector_reg):
    model_t = deduce_t(current_model)
    if not isinstance(model_t, TRecord):
        log.warning("Model is not a record, not marking: %s", model)
        return
    try:
        selector = selector_reg.by_model_t(model_t)
    except KeyError:
        value = None
    else:
        fn_ctx = ctx.clone_with(
            piece=current_model,
            model=current_model,
            **ctx.attributes(ctx.model_state),
            )
        value = selector.pick_fn.call(fn_ctx)
    new_view_piece = htypes.arg_mark.view(
        base=mosaic.put(view.piece),
        model=mosaic.put(current_model),
        value=mosaic.put_opt(value),
        )
    new_state = htypes.context_view.state(
        base=mosaic.put(state),
        )
    new_view = view_reg.animate(new_view_piece, ctx)
    hook.replace_view(new_view, new_state)


@mark.ui_command
def remove_mark(view, state, hook, ctx, view_reg):
    new_view_piece = web.summon(view.piece.base)
    new_state = web.summon(state.base)
    new_view = view_reg.animate(new_view_piece, ctx)
    hook.replace_view(new_view, new_state)
