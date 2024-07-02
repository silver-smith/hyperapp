import logging

from hyperapp.common.htypes import TRecord

from . import htypes
from .services import (
    data_to_ref,
    deduce_t,
    mark,
    mosaic,
    pyobj_creg,
    model_view_creg,
    web,
    )
from .code.command import d_res_ref_to_name
from .code.ui_model_command import change_command
from .code.context_view import ContextView

log = logging.getLogger(__name__)


class RenameCommandContextView(ContextView):

    @classmethod
    def from_piece(cls, piece, model, ctx):
        base_view = model_view_creg.invite(piece.base, model, ctx)
        target_model = web.summon(piece.model)
        command = web.summon(piece.ui_command)
        impl = web.summon(command.impl)
        command_d = pyobj_creg.invite(command.d)
        return cls(base_view, ctx.lcs, target_model, command, impl, command_d)

    def __init__(self, base_view, lcs, model, command_piece, command_impl_piece, command_d):
        super().__init__(base_view, label="Rename command")
        self._lcs = lcs
        self._model = model
        self._command_piece = command_piece
        self._command_impl_piece = command_impl_piece
        self._command_d = command_d

    @property
    def piece(self):
        return htypes.rename_command.view(
            base=mosaic.put(self._base_view.piece),
            model=mosaic.put(self._model),
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

    @property
    def model(self):
        return self._model

    @property
    def command_d_ref(self):
        return self._command_piece.d


def rename_command(piece, current_item, navigator, ctx):
    if current_item is None:
        return None  # Empty command list - no item is selected.
    adapter = htypes.str_adapter.static_str_adapter()
    text_view = htypes.text.edit_view(
        adapter=mosaic.put(adapter),
        )
    new_view_piece = htypes.rename_command.view(
        base=mosaic.put(text_view),
        model=piece.model,
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
def set_command_name(view, widget, lcs):
    name = view.get_text(widget)
    log.info("Set command name for %s: %r", view.model, name)

    def set_name(command):
        d = pyobj_creg.invite(command.d)
        d_t = deduce_t(d)
        new_d_t = TRecord(d_t.module_name, f'{name}_d')
        return htypes.ui.command(
            d=data_to_ref(new_d_t()),
            impl=command.impl,
            )

    change_command(lcs, view.model, view.command_d_ref, set_name)
