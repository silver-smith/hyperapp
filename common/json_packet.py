import datetime
import json
import struct
import socket
import select
import re
import dateutil.parser


class JSONEncoder(json.JSONEncoder):

    def default( self, obj ):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)


packet_size_struct_format = '>I'

def packet_size_size():
    return struct.calcsize(packet_size_struct_format)

def encode_packet_size( size ):
    return struct.pack(packet_size_struct_format, size)

def decode_packet_size( data ):
    return struct.unpack(packet_size_struct_format, data)[0]

def encode_json_packet( value ):
    json_data = json.dumps(value, cls=JSONEncoder)
    return encode_packet(json_data)

def encode_packet( data ):
    return encode_packet_size(len(data)) + data

def is_full_packet( data ):
    ssize = packet_size_size()
    if len(data) < ssize:
        return False
    data_size = decode_packet_size(data[:ssize])
    return len(data) >= ssize + data_size

def decode_packet( data ):
    assert is_full_packet(data)
    ssize = packet_size_size()
    data_size = decode_packet_size(data[:ssize])
    remainder = data[ssize + data_size:]
    json_data = json.loads(data[ssize:ssize + data_size])
    return (json_data, remainder)
