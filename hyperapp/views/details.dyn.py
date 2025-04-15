import logging

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    web,
    )
from .code.mark import mark
from .code.view import Item
from .code.model_command import model_command_ctx
from .code.ui_model_command import split_command_result
from .code.wrapper_view import WrapperView

log = logging.getLogger(__name__)



async def _run_details_command(error_view, ctx, unbound_command, model, model_state):
    command_ctx = model_command_ctx(ctx, model, model_state)
    bound_command = unbound_command.bind(command_ctx)
    try:
        result = await bound_command.run()
    except Exception as x:
        log.exception("Error running details command %r", bound_command)
        result = error_view(x, ctx)
    model, key = split_command_result(result)
    return model


def _details_context(ctx, details_model):
    return ctx.clone_with(
        model=details_model,
        piece=details_model,
        )


class DetailsView(WrapperView):

    @classmethod
    @mark.view
    def from_piece(cls, piece, ctx, view_reg, error_view, command_creg, visualizer):
        unbound_command = command_creg.invite(piece.command)
        details_model = web.summon(piece.details_model)
        details_ctx = _details_context(ctx, details_model)
        details_view = view_reg.invite(piece.details_view, details_ctx)
        return cls(view_reg, error_view, visualizer, unbound_command, details_model, details_view)

    def __init__(self, view_reg, error_view, visualizer, unbound_command, details_model, details_view):
        super().__init__(details_view)
        self._view_reg = view_reg
        self._error_view = error_view
        self._visualizer = visualizer
        self._unbound_command = unbound_command
        self._visualizer = visualizer
        self._details_model = details_model

    @property
    def piece(self):
        return htypes.details.view(
            command=mosaic.put(self._unbound_command.piece),
            details_model=mosaic.put(self._details_model),
            details_view=mosaic.put(self._base_view.piece),
            )

    def children_context(self, ctx):
        return _details_context(ctx, self._details_model)

    def replace_child(self, ctx, widget, idx, new_child_view, new_child_widget):
        # TODO: Save layout.
        super().replace_child(ctx, widget, idx, new_child_view, new_child_widget)

    async def children_changed(self, ctx, rctx, widget):
        log.info("Details view: children changed; updating details view")
        await self._update_details_view(ctx, rctx.model_state, widget)
        pass  # TODO: Save layout.

    def items(self):
        return [Item('base', self._base_view, focusable=False)]

    async def _update_details_view(self, ctx, model_state, widget):
        details_model = await _run_details_command(self._error_view, ctx, self._unbound_command, ctx.model, model_state)
        details_ctx = _details_context(ctx, details_model)
        details_view_piece = self._visualizer(details_ctx, details_model)
        details_view = self._view_reg.animate(details_view_piece, details_ctx)
        details_widget = details_view.construct_widget(None, details_ctx)
        self.replace_child(ctx, widget, 0, details_view, details_widget)
        # Do not update self._details_model - it will cause new layout saving.
        # Calling this hook causes infinite children update.
        # TODO: Possible solution: Add origin to children update and do not call it.
        # self._ctl_hook.element_replaced(0, details_view, details_widget)


@mark.actor.formatter_creg
def format_factory_k(piece, format, command_creg):
    unbound_command = command_creg.invite(piece.command)
    command_d_str = format(unbound_command.d)
    return f"details: {command_d_str}"


@mark.service
def details_commands(global_model_command_reg, get_model_commands, model_t, command_ctx):
    command_list = [
        *global_model_command_reg.values(),
        *get_model_commands(model_t, command_ctx),
        ]
    d_to_command = {
        cmd.d: cmd for cmd in command_list
        if not cmd.properties.is_global or cmd.properties.uses_state
        }
    return d_to_command


def details_command_list(model, model_state, ctx, details_commands):
    model_t = deduce_t(model)
    command_ctx = model_command_ctx(ctx, model, model_state)
    d_to_command = details_commands(model_t, command_ctx)
    factory_k_list = []
    for command in d_to_command.values():
        factory_k = htypes.details.factory_k(
            command=mosaic.put(command.piece),
            )
        factory_k_list.append(factory_k)
    return factory_k_list


async def details_get(k, model, model_state, ctx, error_view, command_creg, visualizer):
    unbound_command = command_creg.invite(k.command)
    details_model = await _run_details_command(error_view, ctx, unbound_command, model, model_state)
    details_ctx = _details_context(ctx, details_model)
    details_view = visualizer(details_ctx, details_model)
    return htypes.details.view(
        command=k.command,
        details_model=mosaic.put(details_model),
        details_view=mosaic.put(details_view),
        )
