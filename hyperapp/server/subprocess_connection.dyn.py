from enum import Enum


class ConnectionEvent(Enum):
    STOP = 1
    EXCEPTION = 2
    PARCEL = 3


class SubprocessRoute:

    def __init__(self, ref_registry, ref_collector_factory, connection):
        self._ref_registry = ref_registry
        self._ref_collector_factory = ref_collector_factory
        self._connection = connection

    def send(self, parcel):
        parcel_ref = self._ref_registry.distil(parcel.piece)
        ref_collector = self._ref_collector_factory()
        parcel_bundle = ref_collector.make_bundle([parcel_ref])
        bundle_cdr = packet_coders.encode('cdr', parcel_bundle)
        self._connection.send((ConnectionEvent.PARCEL.value, bundle_cdr))
