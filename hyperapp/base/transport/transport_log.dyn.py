import itertools
from collections import namedtuple
from datetime import datetime

from .code.mark import mark


Message = namedtuple('Message', [
    'dt',
    'direction',
    'transport_name',
    'msg_bundle',
    'transport_bundle',
    'transport_size',
    ])


class TransportLog:

    def __init__(self):
        self._pending_in = {}
        self._pending_out = {}
        self._messages = {}  # datetime -> Message
        self._counter = itertools.count(1)

    @property
    def messages(self):
        return self._messages

    def add_in_message(self, parcel, transport_name, transport_bundle, transport_size):
        id = next(self._counter)
        dt = datetime.now()
        self._pending_in[parcel] = (id, dt, transport_name, transport_bundle, transport_size)

    def commit_in_message(self, parcel, msg_bundle):
        id, dt, transport_name, transport_bundle, transport_size = self._pending_in.pop(parcel)
        self._messages[id] = Message(
            dt=dt,
            direction='in',
            transport_name=transport_name,
            msg_bundle=msg_bundle,
            transport_bundle=transport_bundle,
            transport_size=transport_size,
            )

    def add_out_message(self, parcel, msg_bundle):
        id = next(self._counter)
        dt = datetime.now()
        self._pending_out[parcel] = (id, dt, msg_bundle)

    def commit_out_message(self, parcel, transport_name, transport_bundle, transport_size):
        id, dt, msg_bundle = self._pending_out.pop(parcel)
        self._messages[id] = Message(
            dt=dt,
            direction='out',
            transport_name=transport_name,
            msg_bundle=msg_bundle,
            transport_bundle=transport_bundle,
            transport_size=transport_size,
            )

@mark.service
def transport_log():
    return TransportLog()
