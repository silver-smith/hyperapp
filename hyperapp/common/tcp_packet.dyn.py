import struct


struct_format = '!Q'


def has_full_tcp_packet(data):
    hsize = struct.calcsize(struct_format)
    if len(data) < hsize:
        return False
    size, = struct.unpack(struct_format, data[:hsize])
    return len(data) >= hsize + size

def decode_tcp_packet(data):
    assert has_full_tcp_packet(data)
    hsize = struct.calcsize(struct_format)
    if len(data) < hsize:
        return False
    size, = struct.unpack(struct_format, data[:hsize])
    packet_data = data[hsize:hsize + size]
    return (packet_data, hsize + size)

def encode_tcp_packet(packet_data):
    header = struct.pack(struct_format, len(packet_data))
    return header + packet_data
