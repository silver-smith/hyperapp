import struct


class Header(object):

    struct_format = '!II'

    @classmethod
    def size( cls ):
        return struct.calcsize(cls.struct_format)

    @classmethod
    def decode( cls, data ):
        encoding_size, contents_size = struct.unpack(cls.struct_format, data)
        return cls(encoding_size, contents_size)

    def __init__( self, encoding_size, contents_size ):
        self.encoding_size = encoding_size
        self.contents_size = contents_size

    def encode( self ):
        return struct.pack(self.struct_format, self.encoding_size, self.contents_size)


class Packet(object):

    @staticmethod
    def is_full( data ):
        hsize = Header.size()
        if len(data) < hsize:
            return False
        header = Header.decode(data[:hsize])
        return len(data) >= hsize + header.encoding_size + header.contents_size

    @classmethod
    def decode( cls, data ):
        assert cls.is_full(data)
        hsize = Header.size()
        header = Header.decode(data[:hsize])
        contents_ofs = hsize + header.encoding_size
        contents_end = contents_ofs + header.contents_size
        encoding = data[hsize:contents_ofs]
        contents = data[contents_ofs:contents_end]
        remainder = data[contents_end:]
        return (cls(encoding, contents), remainder)

    def __init__( self, encoding, contents ):
        assert isinstance(encoding, str), repr(encoding)
        assert isinstance(contents, str), repr(contents)
        self.encoding = encoding
        self.contents = contents

    def encode( self ):
        encoding_size = len(self.encoding)
        contents_size = len(self.contents)
        return Header(encoding_size, contents_size).encode() + self.encoding + self.contents
