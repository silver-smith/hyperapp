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

    def __init__(self, mosaic, ref_collector_factory, connection):
        self._mosaic = mosaic
        self._ref_collector_factory = ref_collector_factory
        self._connection = connection

    def send(self, parcel):
        parcel_ref = self._mosaic.put(parcel.piece)
        ref_collector = self._ref_collector_factory()
        parcel_bundle = ref_collector.make_bundle([parcel_ref])
        bundle_cdr = packet_coders.encode('cdr', parcel_bundle)
        self._connection.send((ConnectionEvent.PARCEL.value, bundle_cdr))
        log.info("Subprocess: parcel is sent: %s", ref_repr(parcel_ref))
