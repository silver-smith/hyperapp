import asyncio
from ..common.htypes import tClientPacket, tServerPacket, tAuxInfo, tPacket
from ..common.transport_packet import tTransportPacket
from ..common.visual_rep import pprint
from ..common.packet_coders import packet_coders
from .request import ResponseBase
from .remoting import Transport
from .tcp_protocol import TcpProtocol


CDR_TRANSPORT_ID = 'tcp.cdr'
JSON_TRANSPORT_ID = 'tcp.json'


def register_transports( registry, services ):
    TcpTransport(services, CDR_TRANSPORT_ID, 'cdr').register(registry)
    TcpTransport(services, JSON_TRANSPORT_ID, 'json').register(registry)


class TcpTransport(Transport):

    def __init__( self, services, transport_id, encoding ):
        Transport.__init__(self, services)
        self.transport_id = transport_id
        self.encoding = encoding

    def register( self, registry ):
        registry.register(self.transport_id, self)

    @asyncio.coroutine
    def send_request_rec( self, remoting, public_key, route, request_or_notification ):
        assert len(route) >= 2, repr(route)  # host and port are expected
        host, port_str = route[:2]
        port = int(port_str)
        transport_packet = self._make_transport_packet(request_or_notification)
        protocol = yield from TcpProtocol.produce(remoting, public_key, host, port)
        protocol.send_packet(transport_packet)
        return True

    def _make_transport_packet( self, request_or_notification ):
        packet = self.make_request_packet(self.encoding, request_or_notification)
        packet_data = packet_coders.encode(self.encoding, packet, tPacket)
        return tTransportPacket(self.transport_id, packet_data)

    @asyncio.coroutine
    def process_packet( self, protocol, session_list, server_public_key, data ):
        packet = packet_coders.decode(self.encoding, data, tPacket)
        pprint(tPacket, packet)
        yield from self.process_aux_info(packet.aux_info)
        response_or_notification_rec = packet_coders.decode(self.encoding, packet.payload, tServerPacket)
        pprint(tServerPacket, response_or_notification_rec)
        return ResponseBase.from_data(server_public_key, self._iface_registry, response_or_notification_rec)
