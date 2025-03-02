from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.wrapper_view import WrapperView


class ModelFieldWrapperView(WrapperView):

    @classmethod
    @mark.view
    def from_piece(cls, piece, ctx, view_reg):
        base_ctx = cls._base_context(ctx, piece.field_name)
        base_view = view_reg.invite(piece.base_view, base_ctx)
        return cls(base_view, piece.field_name)

    @staticmethod
    def _base_context(ctx, field_name):
        return ctx.clone_with(
            model=getattr(ctx.model, field_name)
            )

    def __init__(self, base_view, field_name):
        super().__init__(base_view)
        self._field_name = field_name

    @property
    def piece(self):
        return htypes.model_field_wrapper_view.view(
            base_view=mosaic.put(self._base_view.piece),
            field_name=self._field_name,
            )

    def children_context(self, ctx):
        return self._base_context(ctx, self._field_name)
