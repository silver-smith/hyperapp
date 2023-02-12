import logging
from pathlib import Path

from .services import (
    mark,
    file_bundle,
    generate_rsa_identity,
    identity_registry,
    )

log = logging.getLogger(__name__)


@mark.service
def server_identity():
    bundle = file_bundle(Path.home() / '.local/share/hyperapp/server/identity.json')
    try:
        identity = identity_registry.animate(bundle.load_piece())
        log.info("Server identity: loaded from %s", bundle.path)
        return identity
    except FileNotFoundError:
        identity = generate_rsa_identity()
        bundle.save_piece(identity.piece)
        log.info("Server identity: generated new; saved to %s", bundle.path)
        return identity
