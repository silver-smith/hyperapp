import logging
from enum import Enum

from hyperapp.common.ref import ref_repr
from hyperapp.common.htypes.packet_coders import packet_coders

log = logging.getLogger(__name__)


# Note: copy shared with subprocess_mp_main.py
class ConnectionEvent(Enum):
    STOP = 1
    EXCEPTION = 2
    PARCEL = 3


class SubprocessRoute:

    def __init__(self, mosaic, bundler, connection):
        self._mosaic = mosaic
        self._bundler = bundler
        self._connection = connection

    @property
    def piece(self):
        return None

    @property
    def available(self):
        return True

    def send(self, parcel):
        parcel_ref = self._mosaic.put(parcel.piece)
        parcel_bundle = self._bundler([parcel_ref]).bundle
        bundle_cdr = packet_coders.encode('cdr', parcel_bundle)
        self._connection.send((ConnectionEvent.PARCEL.value, bundle_cdr))
        log.debug("Subprocess: parcel is sent: %s", ref_repr(parcel_ref))
