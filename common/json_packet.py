import datetime
import json
import struct
import socket
import select
import pprint
import re
import dateutil.parser


class JSONEncoder(json.JSONEncoder):

    def default( self, obj ):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)


def json_decoder( obj ):
    if isinstance(obj, basestring):
        # fixme: we decode as datetime all that looks like datetime
        # we must check for 'looks like' explicitly because dateutil.parser may successfully decode strings like: '' or '/'
        if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d+', obj):
            try:
                # dateutil is used to parse datetime because it can detect and parse timezone prefix
                return dateutil.parser.parse(obj)  # will parse timezone too, if included
            except ValueError:
                pass
        return obj
    if isinstance(obj, list):
        return map(json_decoder, obj)
    if isinstance(obj, dict):
        return dict((json_decoder(key), json_decoder(value)) for key, value in obj.items())
    return obj


packet_size_struct_format = '>I'

def packet_size_size():
    return struct.calcsize(packet_size_struct_format)

def encode_packet_size( size ):
    return struct.pack(packet_size_struct_format, size)

def decode_packet_size( data ):
    return struct.unpack(packet_size_struct_format, data)[0]

def encode_packet( value ):
    json_data = json.dumps(value, cls=JSONEncoder)
    return encode_packet_size(len(json_data)) + json_data

def is_full_packet( data ):
    ssize = packet_size_size()
    if len(data) < ssize:
        return False
    data_size = decode_packet_size(data[:ssize])
    return len(data) >= ssize + data_size

def decode_packet( data, decode_datetime=True ):
    assert is_full_packet(data)
    ssize = packet_size_size()
    data_size = decode_packet_size(data[:ssize])
    remainder = data[ssize + data_size:]
    json_data = json.loads(data[ssize:ssize + data_size], object_hook=json_decoder if decode_datetime else None)
    return (json_data, remainder)
