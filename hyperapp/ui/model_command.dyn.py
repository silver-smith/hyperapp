import logging
from functools import partial

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.system_fn import ContextFn
from .code.command import UnboundCommand, BoundCommand
from .code.command_enumerator import UnboundCommandEnumerator
from .code.list_config_ctl import DictListConfigCtl, FlatListConfigCtl

log = logging.getLogger(__name__)


def model_command_ctx(ctx, model, model_state):
    return ctx.push(
        model=model,
        piece=model,
        model_state=model_state,
        **ctx.attributes(model_state),
        )


class ModelCommandFn(ContextFn):

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, system, rpc_system_call_factory):
        return super().from_piece(piece, system, rpc_system_call_factory)

    @property
    def piece(self):
        return htypes.command.model_command_fn(
            function=pyobj_creg.actor_to_ref(self._raw_fn),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )

    def call(self, ctx, **kw):
        result = super().call(ctx, **kw)
        return self._prepare_result(result)

    @staticmethod
    def _prepare_result(result):
        if result is None:
            return result
        if type(result) is tuple and len(result) == 2:
            model, key = result
        else:
            model = result
            key = None
        if type(model) is list:
            model = tuple(model)
        return htypes.command.command_result(
            model=mosaic.put_opt(model),
            key=mosaic.put_opt(key),
            )



class UnboundModelCommand(UnboundCommand):

    def __init__(self, d, ctx_fn, properties):
        super().__init__(d, ctx_fn)
        self._properties = properties

    @property
    def piece(self):
        return htypes.command.model_command(
            d=mosaic.put(self._d),
            properties=self._properties,
            system_fn=mosaic.put(self._ctx_fn.piece),
            )

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


class CommandDict:

    def __init__(self, command_list):
        self._command_list = command_list

    def __getitem__(self, d):
        return self._command_dict[d]

    def values(self):
        return self._command_list

    @property
    def _command_dict(self):
        d_to_command = {}
        for command in self._command_list:
            d_to_command[command.d] = command
        return d_to_command


@mark.service(ctl=FlatListConfigCtl())
def global_model_command_reg(config):
    return CommandDict(config)


@mark.service(ctl=DictListConfigCtl())
def model_command_reg(config, model_t):
    return config.get(model_t, [])


@mark.service(ctl=DictListConfigCtl())
def model_command_enumerator_reg(config, model_t):
    return config.get(model_t, [])


# @mark.service(ctl=FlatListConfigCtl())
# def global_model_command_enumerator_reg(config):
#     return CommandDict(config)


@mark.service
def get_model_commands(model_command_reg, model_command_enumerator_reg, model_t, ctx):
    command_list = [*model_command_reg(model_t)]
    for enumerator in model_command_enumerator_reg(model_t):
        command_list += enumerator.enum_commands(ctx)
    return command_list
