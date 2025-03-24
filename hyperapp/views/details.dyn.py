from . import htypes
from .services import (
    deduce_t,
    mosaic,
    web,
    )
from .code.mark import mark
from .code.model_command import model_command_ctx


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


def details_get(k, ctx):
    pass
