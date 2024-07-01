from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    view_creg,
    web,
    )
from .code.context_view import ContextView


class RenameCommandContextView(ContextView):

    @classmethod
    def from_piece(cls, piece, ctx):
        base_view = view_creg.invite(piece.base, ctx)
        command = web.summon(piece.ui_command)
        impl = web.summon(command.impl)
        command_d = pyobj_creg.invite(command.d)
        return cls(base_view, ctx.lcs, command, impl, command_d)

    def __init__(self, base_view, lcs, command_piece, command_impl_piece, command_d):
        super().__init__(base_view, label="Rename command")
        self._lcs = lcs
        self._command_piece = command_piece
        self._command_impl_piece = command_impl_piece
        self._command_d = command_d

    @property
    def piece(self):
        return htypes.rename_command.view(
            base=mosaic.put(self._base_view.piece),
            ui_command=mosaic.put(self._command_piece),
            )

    def widget_state(self, widget):
        base_widget = self._base_widget(widget)
        base_state = self._base_view.widget_state(base_widget)
        return htypes.rename_command.state(
            base=mosaic.put(base_state),
            )


def rename_command(piece, current_item, navigator, ctx):
    if current_item is None:
        return None  # Empty command list - no item is selected.
    new_view_piece = htypes.rename_command.view(
        base=mosaic.put(navigator.view.piece),
        ui_command=current_item.command,
        )
    new_state = htypes.rename_command.state(
        base=mosaic.put(navigator.state),
        )
    new_view = view_creg.animate(new_view_piece, ctx)
    navigator.hook.replace_view(new_view, new_state)
