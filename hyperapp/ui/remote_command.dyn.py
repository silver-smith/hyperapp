import logging

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    web,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .code.rpc_call import DEFAULT_TIMEOUT
from .code.model_command import UnboundModelCommand, BoundModelCommand
from .code.ui_model_command import split_command_result

log = logging.getLogger(__name__)


def remote_command_wrapper(command_fn_piece, system_fn_creg, **kw):
    command_fn = system_fn_creg.animate(command_fn_piece)
    ctx = Context(**kw)
    result = command_fn.call(ctx)
    if result is None:
        return result
    model, key = split_command_result(result)
    return htypes.command.command_result(
        model=mosaic.put_opt(model),
        key=mosaic.put_opt(key),
        )


class UnboundRemoteCommand(UnboundModelCommand):

    def __init__(self, rpc_system_call_factory, d, ctx_fn, properties, identity, remote_peer):
        super().__init__(d, ctx_fn, properties)
        self._rpc_system_call_factory = rpc_system_call_factory
        self._identity = identity
        self._remote_peer = remote_peer

    def bind(self, ctx):
        return BoundRemoteCommand(
            self._rpc_system_call_factory, self._d, self._ctx_fn, ctx, self._properties, self._identity, self._remote_peer)


class BoundRemoteCommand(BoundModelCommand):

    def __init__(self, rpc_system_call_factory, d, ctx_fn, ctx, properties, identity, remote_peer):
        super().__init__(d, ctx_fn, ctx, properties)
        self._rpc_system_call_factory = rpc_system_call_factory
        self._identity = identity
        self._remote_peer = remote_peer

    async def _run(self):
        try:
            model = self._ctx.model
        except KeyError:
            ctx = self._ctx
        else:
            if isinstance(model, htypes.model.remote_model):
                real_model = web.summon(model.model)
                ctx = self._ctx.clone_with(
                    model=real_model,
                    piece=real_model,
                    )
            else:
                ctx = self._ctx
        log.info("Run remote command: %r", self)
        wrapper_fn = ContextFn(
            rpc_system_call_factory=self._rpc_system_call_factory,
            ctx_params=('command_fn_piece', *self._ctx_fn.ctx_params),
            service_params=('system_fn_creg',),
            raw_fn=remote_command_wrapper,
            )
        result = wrapper_fn.rpc_call(
            receiver_peer=self._remote_peer,
            sender_identity=self._identity,
            ctx=ctx,
            command_fn_piece=self._ctx_fn.piece,
            )
        log.info("Run remote command %r result: [%s] %r", self, type(result), result)
        return result


@mark.service
def remote_command_from_model_command(rpc_system_call_factory, identity, remote_peer, command):
    return UnboundRemoteCommand(rpc_system_call_factory, command.d, command.fn, command.properties, identity, remote_peer)


@mark.command_enum
def remote_command_enum(piece, identity, ctx, peer_registry, get_model_commands, remote_command_from_model_command):
    model, model_t = web.summon_with_t(piece.model)
    remote_peer = peer_registry.invite(piece.remote_peer)
    command_list = get_model_commands(model_t, ctx)
    return [
        remote_command_from_model_command(identity, remote_peer, command)
        for command in command_list
        ]
