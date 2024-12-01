from functools import partial

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.context_view import ContextView


class CommandLayoutContextView(ContextView):

    @classmethod
    @mark.actor.view_creg
    def from_piece(cls, piece, ctx, data_to_ref, view_creg, custom_ui_model_commands):
        base_view = view_creg.invite(piece.base, ctx)
        if piece.model_t is not None:
            model_t = pyobj_creg.invite(piece.model_t)
        else:
            model_t = None
        ui_command_d = pyobj_creg.invite(piece.ui_command_d)
        model_command_d = pyobj_creg.invite(piece.model_command_d)
        return cls(data_to_ref, custom_ui_model_commands, base_view, ctx.lcs, model_t, ui_command_d, model_command_d)

    def __init__(self, data_to_ref, custom_ui_model_commands, base_view, lcs, model_t, ui_command_d, model_command_d):
        super().__init__(base_view, label="Command layout")
        self._data_to_ref = data_to_ref
        self._custom_commands = custom_ui_model_commands(lcs, model_t)
        self._model_t = model_t
        self._ui_command_d = ui_command_d
        self._model_command_d = model_command_d

    @property
    def piece(self):
        return htypes.command_layout_context.view(
            base=mosaic.put(self._base_view.piece),
            model_t=pyobj_creg.actor_to_ref(self._model_t) if self._model_t is not None else None,
            ui_command_d=self._data_to_ref(self._ui_command_d),
            model_command_d=self._data_to_ref(self._model_command_d),
            )

    def _set_layout(self, layout):
        command = htypes.command.ui_model_command(
            ui_command_d=self._data_to_ref(self._ui_command_d),
            model_command_d=self._data_to_ref(self._model_command_d),
            layout=mosaic.put(layout),
            )
        self._custom_commands.set(command)

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
    if isinstance(piece, htypes.model_commands.view):
        model_t = deduce_t(web.summon(piece.model))
        model_t_ref = pyobj_creg.actor_to_ref(model_t)
    else:
        assert isinstance(piece, htypes.global_commands.view)
        model_t_ref = None
    new_view_piece = htypes.command_layout_context.view(
        base=mosaic.put(navigator.view.piece),
        model_t=model_t_ref,
        ui_command_d=current_item.ui_command_d,
        model_command_d=current_item.model_command_d,
        )
    new_state = htypes.command_layout_context.state(
        base=mosaic.put(navigator.state),
        )
    new_view = view_creg.animate(new_view_piece, ctx)
    navigator.hook.replace_view(new_view, new_state)
