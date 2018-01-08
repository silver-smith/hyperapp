import logging
from queue import Queue

from ..common.interface import packet as packet_types
from ..common.request import Update
from ..common.transport_packet import tTransportPacket
from ..common.packet_coders import packet_coders
from ..common.visual_rep import pprint
from .module import Module
from .request import PeerChannel, Peer, ServerNotification
from .remoting import Transport
from .transport_session import TransportSession

log = logging.getLogger(__name__)


MODULE_NAME = 'tcp_transport'


class TcpChannel(PeerChannel):

    def __init__(self, transport):
        self.transport = transport
        self.updates = Queue()  # Update list

    def _pop_all(self):
        updates = []
        while not self.updates.empty():
            updates.append(self.updates.get())
        return list(reversed(updates))

    def send_update(self, update):
        assert isinstance(update, Update), repr(update)
        log.info('    update to be sent to %r channel %s', self.transport.get_transport_id(), self.get_id())
        self.updates.put(update)

    def pop_updates(self):
        return self._pop_all()


class TcpSession(TransportSession):

    def __init__(self, transport):
        assert isinstance(transport, TcpTransport), repr(transport)
        TransportSession.__init__(self)
        self.transport = transport
        self.channel = TcpChannel(transport)

    def pull_notification_transport_packets(self):
        updates = self.channel._pop_all()
        if not updates:
            return []
        notification = ServerNotification(self.transport._error_types, packet_types)
        for update in updates:
            notification.add_update(update)
        log.info('-- sending notification to %r channel %s', self.transport.get_transport_id(), self.get_id())
        notification_packet = self.transport.make_notification_packet(self.transport.encoding, notification)
        packet_data = packet_coders.encode(self.transport.encoding, notification_packet, packet_types.packet)
        return [tTransportPacket(self.transport.get_transport_id(), packet_data)]


class TcpTransport(Transport):

    def __init__(self, encoding, services):
        Transport.__init__(self, services)
        self.encoding = encoding

    def get_transport_id(self):
        return 'tcp.%s' % self.encoding

    def register(self, registry):
        registry.register(self.get_transport_id(), self)

    def process_packet(self, iface_registry, server, session_list, data):
        session = session_list.get_transport_session(self.get_transport_id())
        if session is None:
           session = TcpSession(self)
           session_list.set_transport_session(self.get_transport_id(), session) 
        request_packet = packet_coders.decode(self.encoding, data, packet_types.packet)
        response_packet = self.process_request_packet(iface_registry, server, Peer(session.channel), self.encoding, request_packet)
        if response_packet is None:
            return []
        packet_data = packet_coders.encode(self.encoding, response_packet, packet_types.packet)
        return [packet_data]


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, MODULE_NAME)
        TcpTransport('cdr', services).register(services.remoting.transport_registry)
        TcpTransport('json', services).register(services.remoting.transport_registry)
