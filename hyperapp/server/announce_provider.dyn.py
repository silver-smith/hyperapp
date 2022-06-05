import logging
from functools import partial

from hyperapp.common.module import Module

from . import htypes

_log = logging.getLogger(__name__)


def aux_bundler_hook(mosaic, impl_registry, server_peer_ref, ref, t, value):
    try:
        ctr_fn, spec = impl_registry[t]
    except KeyError:
        return
    _log.info("Announce provider for service %s: %s", value, server_peer_ref)
    service_provider = htypes.impl.service_provider(ref, server_peer_ref)
    yield mosaic.put(service_provider)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        server_peer_ref = services.mosaic.put(
            services.server_identity.peer.piece)
        services.aux_bundler_hooks.append(
            partial(aux_bundler_hook, services.mosaic, services.impl_registry, server_peer_ref))
