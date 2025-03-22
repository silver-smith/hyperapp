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


class MarkView(ContextView):

    @classmethod
    @mark.view
    def from_piece(cls, piece, ctx, format, view_reg):
        base_view = view_reg.invite(piece.base, ctx)
        model = web.summon(piece.model)
        model_label = format(model)
        return cls(base_view, model, model_label)

    def __init__(self, base_view, model, model_label):
        model_t = deduce_t(model)
        super().__init__(base_view, label=f"Mark: {model_label}")
        self._model = model
        self._mark_name = f'mark-{model_t.module_name}-{model_t.name}'

    @property
    def piece(self):
        return htypes.arg_mark.view(
            base=mosaic.put(self._base_view.piece),
            model=mosaic.put(self._model),
            )

    def children_context(self, ctx):
        return ctx.clone_with(
            **{self._mark_name: self._model},
            )


@mark.ui_command
def add_mark(view, state, hook, current_model, ctx, view_reg):
    model_t = deduce_t(current_model)
    if not isinstance(model_t, TRecord):
        log.warning("Model is not a record, not marking: %s", model)
        return
    new_view_piece = htypes.arg_mark.view(
        base=mosaic.put(view.piece),
        model=mosaic.put(current_model)
        )
    new_state = htypes.context_view.state(
        base=mosaic.put(state),
        )
    new_view = view_reg.animate(new_view_piece, ctx)
    hook.replace_view(new_view, new_state)
