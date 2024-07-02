import logging

from . import htypes
from .services import (
    mark,
    mosaic,
    pyobj_creg,
    model_view_creg,
    web,
    )
from .code.context_view import ContextView
from .code.command import d_res_ref_to_name

log = logging.getLogger(__name__)


class RenameCommandContextView(ContextView):

    @classmethod
    def from_piece(cls, piece, model, ctx):
        base_view = model_view_creg.invite(piece.base, model, ctx)
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

    def get_text(self, widget):
        base_widget = self._base_widget(widget)
        return self._base_view.get_text(base_widget)


def rename_command(piece, current_item, navigator, ctx):
    if current_item is None:
        return None  # Empty command list - no item is selected.
    adapter = htypes.str_adapter.static_str_adapter()
    text_view = htypes.text.edit_view(
        adapter=mosaic.put(adapter),
        )
    new_view_piece = htypes.rename_command.view(
        base=mosaic.put(text_view),
        ui_command=current_item.command,
        )
    text_state = htypes.text.state()
    new_state = htypes.rename_command.state(
        base=mosaic.put(text_state),
        )
    command = web.summon(current_item.command)
    name = d_res_ref_to_name(command.d)
    new_view = model_view_creg.animate(new_view_piece, name, ctx)
    navigator.view.open(ctx, name, new_view, navigator.widget_wr())


@mark.ui_command(htypes.rename_command.view)
def set_command_name(view, widget):
    text = view.get_text(widget)
    log.info("Set command name: %r", text)
