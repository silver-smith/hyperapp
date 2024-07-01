from . import htypes
from .services import (
    mark,
    mosaic,
    pyobj_creg,
    set_ui_model_command_layout,
    get_ui_model_commands,
    set_ui_model_commands,
    view_creg,
    web,
    )
from .code.context_view import ContextView


class CommandLayoutContextView(ContextView):

    @classmethod
    def from_piece(cls, piece, ctx):
        base_view = view_creg.invite(piece.base, ctx)
        model = web.summon(piece.model)
        command = web.summon(piece.ui_command)
        impl = web.summon(command.impl)
        command_d = pyobj_creg.invite(command.d)
        return cls(base_view, ctx.lcs, model, command, impl, command_d)

    def __init__(self, base_view, lcs, model, command_piece, command_impl_piece, command_d):
        super().__init__(base_view, label="Command layout")
        self._lcs = lcs
        self._model = model
        self._command_piece = command_piece
        self._command_impl_piece = command_impl_piece
        self._command_d = command_d

    @property
    def piece(self):
        return htypes.command_layout_context.view(
            base=mosaic.put(self._base_view.piece),
            model=mosaic.put(self._model),
            ui_command=mosaic.put(self._command_piece),
            )

    def _set_layout(self, layout):
        if isinstance(self._command_impl_piece, htypes.ui.external_ui_model_command_impl):
            set_ui_model_command_layout(self._lcs, self._command_d, layout)
        else:
            self._update_command_layout(layout)

    def _update_command_layout(self, layout):
        command_list = get_ui_model_commands(self._lcs, self._model)
        idx, command = self._find_command(command_list)
        new_impl = htypes.ui.ui_model_command_impl(
            model_command_impl=self._command_impl_piece.model_command_impl,
            layout=mosaic.put(layout),
            )
        new_command = htypes.ui.command(
            d=self._command_piece.d,
            impl=mosaic.put(new_impl),
            )
        command_list = command_list.copy()
        command_list[idx] = new_command
        set_ui_model_commands(self._lcs, self._model, command_list)

    def _find_command(self, command_list):
        for idx, command in enumerate(command_list):
            if command.d == self._command_piece.d:
                return (idx, command)
        raise RuntimeError(f"Command {self._command_d} is missing from configured in LCS for model {self._model}")

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


def open_command_layout_context(piece, current_item, navigator, ctx):
    new_view_piece = htypes.command_layout_context.view(
        base=mosaic.put(navigator.view.piece),
        model=piece.model,
        ui_command=current_item.command,
        )
    new_state = htypes.command_layout_context.state(
        base=mosaic.put(navigator.state),
        )
    new_view = view_creg.animate(new_view_piece, ctx)
    navigator.hook.replace_view(new_view, new_state)
