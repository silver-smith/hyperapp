from functools import partial

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.ui_model_command import change_command
from .code.context_view import ContextView


class CommandLayoutContextView(ContextView):

    @classmethod
    @mark.actor.view_creg
    def from_piece(cls, piece, ctx, data_to_ref, view_creg):
        base_view = view_creg.invite(piece.base, ctx)
        model = web.summon(piece.model)
        command_d = pyobj_creg.invite(piece.ui_command_d)
        return cls(data_to_ref, base_view, ctx.lcs, model, command_d)

    def __init__(self, data_to_ref, base_view, lcs, model, command_d):
        super().__init__(base_view, label="Command layout")
        self._data_to_ref = data_to_ref
        self._lcs = lcs
        self._model = model
        self._command_d = command_d

    @property
    def piece(self):
        return htypes.command_layout_context.view(
            base=mosaic.put(self._base_view.piece),
            model=mosaic.put(self._model),
            ui_command_d=self._data_to_ref(self._command_d),
            )

    def _set_layout(self, layout):
        if isinstance(self._command_impl_piece, htypes.ui.external_ui_model_command_impl):
            set_ui_model_command_layout(self._lcs, self._command_d, layout)
        else:
            change_command(self._lcs, self._model, self._command_piece.d,
                           partial(self._command_with_new_layout, layout))

    def _command_with_new_layout(self, layout, command):
        new_impl = htypes.ui.ui_model_command_impl(
            model_command_impl=self._command_impl_piece.model_command_impl,
            layout=mosaic.put(layout),
            )
        return htypes.ui.ui_command(
            d=self._command_piece.d,
            impl=mosaic.put(new_impl),
            )

    def children_context(self, ctx):
        return ctx.clone_with(
            set_layout=self._set_layout,
            )

    def widget_state(self, widget):
        base_widget = self._base_widget(widget)
        base_state = self._base_view.widget_state(base_widget)
        return htypes.command_layout_context.state(
            base=mosaic.put(base_state),
            )


@mark.command
def open_command_layout_context(piece, current_item, navigator, ctx, view_creg):
    new_view_piece = htypes.command_layout_context.view(
        base=mosaic.put(navigator.view.piece),
        model=piece.model,
        ui_command_d=current_item.command_d,
        )
    new_state = htypes.command_layout_context.state(
        base=mosaic.put(navigator.state),
        )
    new_view = view_creg.animate(new_view_piece, ctx)
    navigator.hook.replace_view(new_view, new_state)
