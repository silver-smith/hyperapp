import logging
from functools import partial

from . import htypes
from .services import (
    aux_bundler_hooks,
    impl_registry,
    mosaic,
    server_identity,
    )

_log = logging.getLogger(__name__)


def aux_bundler_hook(server_peer_ref, ref, t, value):
    try:
        ctr_fn, spec = impl_registry[t]
    except KeyError:
        return
    _log.info("Announce provider for service %s: %s, spec: %s", value, server_peer_ref, spec)
    service_provider = htypes.impl.service_provider(
        service=ref,
        provider=server_peer_ref,
        servant=mosaic.put(value),
        spec=mosaic.put(spec),
        )
    yield mosaic.put(service_provider)


def init_server_provider_announcer():
    server_peer_ref = mosaic.put(server_identity.peer.piece)
    aux_bundler_hooks.append(partial(aux_bundler_hook, server_peer_ref))
