import logging

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    web,
    )
from .code.mark import mark
from .code.model_command import model_command_ctx
from .code.wrapper_view import WrapperView

log = logging.getLogger(__name__)



async def _run_details_command(ctx, unbound_command):
    command_ctx = model_command_ctx(ctx, ctx.model, ctx.model_state)
    bound_command = unbound_command.bind(command_ctx)
    return await bound_command.run()


def _details_context(ctx, details_model):
    return ctx.clone_with(
        model=details_model,
        piece=details_model,
        )


def _pick_details_command(details_commands, ctx, command_d, model, model_state):
    model_t = deduce_t(model)
    command_ctx = model_command_ctx(ctx, model, model_state)
    d_to_command = details_commands(model_t, command_ctx)
    unbound_command = d_to_command[command_d]
    return unbound_command


class DetailsView(WrapperView):

    @classmethod
    @mark.view
    def from_piece(cls, piece, ctx, view_reg, visualizer, details_commands):
        details_model = web.summon(piece.details_model)
        details_ctx = ctx.clone_with(
            model=details_model,
            piece=details_model,
            )
        details_view = view_reg.invite(piece.details_view, details_ctx)
        command_d = web.summon(piece.command_d)
        unbound_command = _pick_details_command(details_commands, ctx, command_d, ctx.model, ctx.model_state)
        return cls(visualizer, details_model, details_view, unbound_command)

    def __init__(self, visualizer, details_model, details_view, unbound_command):
        super().__init__(details_view)
        self._visualizer = visualizer
        self._details_model = details_model
        self._unbound_command = unbound_command

    @property
    def piece(self):
        return htypes.details.view(
            details_model=mosaic.put(self._details_model),
            details_view=mosaic.put(self._base_view.piece),
            command_d=mosaic.put(self._unbound_command.d),
            )

    def children_context(self, ctx):
        return _details_context(ctx, self._details_model)

    def replace_child(self, ctx, widget, idx, new_child_view, new_child_widget):
        pass  # TODO: Save layout.

    async def children_changed(self, ctx, rctx, widget):
        log.info("Details view: children changed")
        pass  # TODO: Save layout.


@mark.actor.formatter_creg
def format_factory_k(piece, format):
    command_d = web.summon(piece.command_d)
    command_d_str = format(command_d)
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
    for command_d in d_to_command:
        factory_k = htypes.details.factory_k(
            command_d=mosaic.put(command_d),
            )
        factory_k_list.append(factory_k)
    return factory_k_list


async def details_get(k, model, model_state, ctx, visualizer, details_commands):
    command_d = web.summon(k.command_d)
    unbound_command = _pick_details_command(details_commands, ctx, command_d, model, model_state)
    details_model = await _run_details_command(ctx, unbound_command)
    details_ctx = _details_context(ctx, details_model)
    details_view = visualizer(details_ctx, details_model)
    return htypes.details.view(
        details_model=mosaic.put(details_ctx.model),
        details_view=mosaic.put(details_view),
        command_d=k.command_d,
        )
