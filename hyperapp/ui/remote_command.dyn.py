import logging

from .services import (
    deduce_t,
    web,
    )
from .code.mark import mark
from .code.model_command import UnboundModelCommand, BoundModelCommand

log = logging.getLogger(__name__)


class UnboundRemoteCommand(UnboundModelCommand):

    def __init__(self, rpc_call_factory, d, ctx_fn, properties, identity, remote_peer):
        super().__init__(d, ctx_fn, properties)
        self._rpc_call_factory = rpc_call_factory
        self._identity = identity
        self._remote_peer = remote_peer

    def bind(self, ctx):
        return BoundRemoteCommand(
            self._rpc_call_factory, self._d, self._ctx_fn, ctx, self._properties, self._identity, self._remote_peer)


class BoundRemoteCommand(BoundModelCommand):

    def __init__(self, rpc_call_factory, d, ctx_fn, ctx, properties, identity, remote_peer):
        super().__init__(d, ctx_fn, ctx, properties)
        self._rpc_call_factory = rpc_call_factory
        self._identity = identity
        self._remote_peer = remote_peer

    async def _run(self):
        try:
            model = self._ctx.model
        except KeyError:
            ctx = self._ctx
        else:
            real_model = web.summon(model.model)
            ctx = self._ctx.clone_with(
                model=real_model,
                piece=real_model,
                )
        log.info("Run remote command: %r", self)
        rpc_call = self._rpc_call_factory(
            sender_identity=self._identity,
            receiver_peer=self._remote_peer,
            servant_ref=self._ctx_fn.partial_ref(ctx),
            )
        result = rpc_call()
        log.info("Run remote command %r result: [%s] %r", self, type(result), result)
        return result


@mark.command_enum
def remote_command_enum(piece, identity, peer_registry, rpc_call_factory, model_command_reg):
    model, model_t = web.summon_with_t(piece.model)
    remote_peer = peer_registry.invite(piece.remote_peer)
    command_list = model_command_reg(model_t)
    return [
        UnboundRemoteCommand(rpc_call_factory, cmd.d, cmd.fn, cmd.properties, identity, remote_peer)
        for cmd in command_list
        ]
