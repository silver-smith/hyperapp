import logging
from functools import partial

from hyperapp.common.module import Module

from . import htypes

_log = logging.getLogger(__name__)


def register_service_provider(piece, web, peer_registry, service_provider_reg):
    service = web.summon(piece.service)
    server_peer = peer_registry.invite(piece.provider)
    spec = web.summon(piece.spec)
    service_provider_reg[service] = (server_peer, piece.servant, spec)
    _log.info("Service %s is provided by: %s, servant %s, spec %s", service, server_peer, piece.servant, spec)


def aux_unbundler_hook(web, peer_registry, service_provider_reg, ref, t, value):
    if t is htypes.impl.service_provider:
        register_service_provider(value, web, peer_registry, service_provider_reg)
        return True
    else:
        return False


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.service_provider_reg = {}  # service piece value -> (provider peer, servant ref, spec)
        services.meta_registry.register_actor(
            htypes.impl.service_provider, register_service_provider, services.web, services.peer_registry, services.service_provider_reg)
        services.aux_unbundler_hooks.append(
            partial(aux_unbundler_hook, services.web, services.peer_registry, services.service_provider_reg))
