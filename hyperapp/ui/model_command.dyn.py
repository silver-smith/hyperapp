import logging
from functools import partial

from .services import (
    deduce_t,
    web,
    )
from .code.mark import mark
from .code.command import UnboundCommand, BoundCommand
from .code.command_enumerator import UnboundCommandEnumerator
from .code.command_config_ctl import TypedCommandConfigCtl, UntypedCommandConfigCtl

log = logging.getLogger(__name__)


def model_command_ctx(ctx, model, model_state):
    return ctx.push(
        model=model,
        piece=model,
        model_state=model_state,
        **ctx.attributes(model_state),
        )


class UnboundModelCommand(UnboundCommand):

    def __init__(self, d, ctx_fn, properties):
        super().__init__(d, ctx_fn)
        self._properties = properties

    @property
    def properties(self):
        return self._properties

    def bind(self, ctx):
        return BoundModelCommand(self._d, self._ctx_fn, ctx, self._properties)


class BoundModelCommand(BoundCommand):

    def __init__(self, d, ctx_fn, ctx, properties):
        super().__init__(d, ctx_fn, ctx)
        self._properties = properties

    @property
    def properties(self):
        return self._properties


@mark.actor.command_creg
def model_command_from_piece(piece, system_fn_creg):
    ctx_fn = system_fn_creg.invite(piece.system_fn)
    return UnboundModelCommand(
        d=web.summon(piece.d),
        ctx_fn=ctx_fn,
        properties=piece.properties,
        )


@mark.actor.command_creg
def model_command_enumerator_from_piece(piece, system_fn_creg):
    ctx_fn = system_fn_creg.invite(piece.system_fn)
    return UnboundCommandEnumerator(
        ctx_fn=ctx_fn,
        )


@mark.service(ctl=UntypedCommandConfigCtl())
def global_model_command_reg(config):
    return config


@mark.service(ctl=TypedCommandConfigCtl())
def model_command_reg(config, model_t):
    return config.get(model_t, [])


@mark.service(ctl=TypedCommandConfigCtl())
def model_command_enumerator_reg(config, model_t):
    return config.get(model_t, [])


@mark.service
def get_model_commands(model_command_reg, model_command_enumerator_reg, model_t, ctx):
    command_list = [*model_command_reg(model_t)]
    for enumerator in model_command_enumerator_reg(model_t):
        command_list += enumerator.enum_commands(ctx)
    return command_list
