import logging
from pathlib import Path

from hyperapp.common.interface import encrypted_transport as encrypted_transport_types
from hyperapp.common.ref import make_object_ref
from hyperapp.common.identity import Identity
from ..module import Module

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.encrypted'
IDENTITY_PATH = '~/.local/share/hyperapp/server/transport/encrypted/identity.pem'


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, MODULE_NAME)
        self._identity = self._produce_identity()
        address = encrypted_transport_types.address(
            public_key_der=self._identity.public_key.to_der(),
            base_transport_ref=services.tcp_transport_ref)
        services.encrypted_transport_ref = services.ref_registry.register_object(encrypted_transport_types.address, address)

    @staticmethod
    def _produce_identity():
        identity_path = Path(IDENTITY_PATH).expanduser()
        if identity_path.is_file():
            identity = Identity.load_from_file(identity_path)
        else:
            identity = Identity.generate()
            identity.save_to_file(identity_path, create_dirs=True)
            log.info('Generated new identity; saved to %s', identity_path)
        return identity
