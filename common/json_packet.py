import datetime
import json
import struct
import socket
import select
import re
import dateutil.parser


class Header(object):

    struct_format = '>II'

    def __init__( self, encoding_size, contents_size ):
        self.encoding_size = encoding_size
        self.contents_size = contents_size

    @classmethod
    def size( cls ):
        return struct.calcsize(cls.struct_format)

    def encode( self ):
        return struct.pack(self.struct_format, self.encoding_size, self.contents_size)

    @classmethod
    def decode( cls, data ):
        encoding_size, contents_size = struct.unpack(cls.struct_format, data)
        return cls(encoding_size, contents_size)


def encode_packet( encoding, contents ):
    assert isinstance(encoding, str), repr(encoding)
    assert isinstance(contents, str), repr(contents)
    encoding_size = len(encoding)
    contents_size = len(contents)
    return Header(encoding_size, contents_size).encode() + encoding + contents

def is_full_packet( data ):
    hsize = Header.size()
    if len(data) < hsize:
        return False
    header = Header.decode(data[:hsize])
    return len(data) >= hsize + header.encoding_size + header.contents_size

def decode_packet( data ):
    assert is_full_packet(data)
    hsize = Header.size()
    header = Header.decode(data[:hsize])
    contents_ofs = hsize + header.encoding_size
    contents_end = contents_ofs + header.contents_size
    encoding = data[hsize:contents_ofs]
    contents = data[contents_ofs:contents_end]
    remainder = data[contents_end:]
    return (encoding, contents, remainder)
