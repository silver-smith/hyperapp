import struct

from ..common.interface import hyper_ref as href_types
from .packet_coders import packet_coders


struct_format = '!QQ'


def has_full_tcp_packet(data):
    header_size = struct.calcsize(struct_format)
    if len(data) < header_size:
        return False
    encoding_size, size = struct.unpack(struct_format, data[:header_size])
    return len(data) >= header_size + encoding_size + size

def decode_tcp_packet(data):
    assert has_full_tcp_packet(data)
    header_size = struct.calcsize(struct_format)
    encoding_size, size = struct.unpack(struct_format, data[:header_size])
    encoding = data[header_size:header_size + encoding_size].decode()
    packet_data = data[header_size + encoding_size:header_size + encoding_size + size]
    bundle = packet_coders.decode(encoding, packet_data, href_types.bundle)
    return (bundle, header_size + encoding_size + size)

def encode_tcp_packet(bundle, encoding):
    assert isinstance(bundle, href_types.bundle), repr(bundle)
    packet_data = packet_coders.encode(encoding, bundle, href_types.bundle)
    encoded_encoding = encoding.encode()
    header = struct.pack(struct_format, len(encoded_encoding), len(packet_data))
    return header + encoded_encoding + packet_data
