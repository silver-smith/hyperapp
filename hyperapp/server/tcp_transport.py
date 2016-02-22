from ..common.htypes import tClientPacket, tServerPacket, iface_registry
from ..common.packet import tAuxInfo, tPacket, Packet
from ..common.packet_coders import packet_coders
from ..common.visual_rep import pprint
from .request import RequestBase
from .transport import Transport, transport_registry


class TcpChannel(object):

    def __init__( self ):
        pass


class TcpTransport(Transport):

    def __init__( self, encoding ):
        self.encoding = encoding

    def process_packet( self, server, peer, data ):
        packet = packet_coders.decode(self.encoding, data, tPacket)
        request_rec = packet_coders.decode(self.encoding, packet.payload, tClientPacket)
        pprint(tClientPacket, request_rec)
        request = RequestBase.from_data(peer, TcpChannel(), iface_registry, request_rec)
        result = server.process_request(request)
        if result is None:
            return
        aux_info, response_or_notification = result
        pprint(tAuxInfo, aux_info)
        pprint(tServerPacket, response_or_notification)
        payload = packet_coders.encode(self.encoding, response_or_notification, tServerPacket)
        packet = Packet(aux_info, payload)
        packet_data = packet_coders.encode(self.encoding, packet, tPacket)
        return packet_data


transport_registry.register('tcp.cdr', TcpTransport('cdr'))
transport_registry.register('tcp.json', TcpTransport('json'))
