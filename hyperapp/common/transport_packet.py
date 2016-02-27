from .htypes import tString, tBinary, Field, TRecord
from .packet_coders import packet_coders


tTransportPacket = TRecord([
    Field('transport_id', tString),
    Field('data', tBinary),
    ])


ENCODING = 'cdr'


def encode_transport_packet( packet ):
    return packet_coders.encode(ENCODING, packet, tTransportPacket)

def decode_transport_packet( data ):
    return packet_coders.decode(ENCODING, data, tTransportPacket)
