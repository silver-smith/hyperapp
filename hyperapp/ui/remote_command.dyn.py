import logging

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    web,
    )
from .code.mark import mark
from .code.model_command import UnboundModelCommand, BoundModelCommand

log = logging.getLogger(__name__)


class UnboundRemoteCommand(UnboundModelCommand):

    def __init__(self, d, ctx_fn, properties, remote_peer):
        super().__init__(d, ctx_fn, properties)
        self._remote_peer = remote_peer

    def bind(self, ctx):
        return BoundRemoteCommand(self._d, self._ctx_fn, ctx, self._properties, self._remote_peer)


class BoundRemoteCommand(BoundModelCommand):

    def __init__(self, d, ctx_fn, ctx, properties, remote_peer):
        super().__init__(d, ctx_fn, ctx, properties)
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
        result = await self._ctx_fn.call(ctx, remote_peer=self._remote_peer)
        log.info("Run remote command %r result: [%s] %r", self, type(result), result)
        return result


@mark.service
def remote_command_from_model_command(remote_peer, command):
    return UnboundRemoteCommand(command.d, command.fn, command.properties, remote_peer)


@mark.command_enum
def remote_command_enum(piece, ctx, peer_registry, get_model_commands, remote_command_from_model_command):
    model, model_t = web.summon_with_t(piece.model)
    remote_peer = peer_registry.invite(piece.remote_peer)
    command_list = get_model_commands(model_t, ctx)
    return [
        remote_command_from_model_command(remote_peer, command)
        for command in command_list
        ]
