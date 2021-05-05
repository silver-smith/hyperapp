import logging
from pathlib import Path

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.server_identity = self._produce_identity(services)

    def _produce_identity(self, services):
        bundle = services.file_bundle(Path.home() / '.local/share/hyperapp/server/identity.json')
        try:
            identity = services.identity_registry.animate(bundle.load_piece())
            log.info("Server identity: loaded from %s", bundle.path)
            return identity
        except FileNotFoundError:
            identity = services.generate_rsa_identity()
            bundle.save_piece(identity.piece)
            log.info("Server identity: generated new; saved to %s", bundle.path)
            return identity
