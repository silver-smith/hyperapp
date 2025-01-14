import struct

from hyperapp.boot.htypes import bundle_t
from hyperapp.boot.htypes.packet_coders import packet_coders


# utf-8 encoded encoding size, packet data size
STRUCT_FORMAT = '!QQ'
TCP_BUNDLE_ENCODING = 'cdr'


def address_to_str(address):
    if address is None:
        return 'None'
    host, port = address
    return f'{host}:{port}'


def has_full_tcp_packet(data):
    header_size = struct.calcsize(STRUCT_FORMAT)
    if len(data) < header_size:
        return False
    encoding_size, size = struct.unpack(STRUCT_FORMAT, data[:header_size])
    return len(data) >= header_size + encoding_size + size


def decode_tcp_packet(data):
    assert has_full_tcp_packet(data)
    header_size = struct.calcsize(STRUCT_FORMAT)
    encoding_size, size = struct.unpack(STRUCT_FORMAT, data[:header_size])
    encoding = data[header_size:header_size + encoding_size].decode()
    packet_data = data[header_size + encoding_size:header_size + encoding_size + size]
    bundle = packet_coders.decode(encoding, packet_data, bundle_t)
    return (bundle, header_size + encoding_size + size)


def encode_tcp_packet(bundle):
    assert isinstance(bundle, bundle_t), repr(bundle)
    encoding = TCP_BUNDLE_ENCODING
    packet_data = packet_coders.encode(encoding, bundle)
    encoded_encoding = encoding.encode()
    header = struct.pack(STRUCT_FORMAT, len(encoded_encoding), len(packet_data))
    return header + encoded_encoding + packet_data
