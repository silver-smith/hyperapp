import struct
from .interface import tString, Field, TRecord, TList
from .packet_coders import packet_coders
from .request import decode_server_packet, decode_client_packet


tModuleDep = TRecord([
    Field('module_id', tString),
    Field('visible_as', tString),
    ])

ModuleDep = tModuleDep.instantiate


tModule = TRecord([
    Field('id', tString),  # uuid
    Field('package', tString),  # like 'hyperapp.client'
    Field('deps', TList(tModuleDep)),
    Field('source', tString),
    Field('fpath', tString),
    ])

Module = tModule.instantiate


tRequirement = TList(tString)  # [hierarchy id, class id]

tAuxInfo = TRecord([
    Field('requirements', TList(tRequirement)),
    Field('modules', TList(tModule)),
    ])

AuxInfo = tAuxInfo.instantiate


class Header(object):

    struct_format = '!III'

    @classmethod
    def size( cls ):
        return struct.calcsize(cls.struct_format)

    @classmethod
    def decode( cls, data ):
        encoding_size, aux_size, contents_size = struct.unpack(cls.struct_format, data)
        return cls(encoding_size, aux_size, contents_size)

    def __init__( self, encoding_size, aux_size, contents_size ):
        self.encoding_size = encoding_size
        self.aux_size = aux_size
        self.contents_size = contents_size

    def encode( self ):
        return struct.pack(self.struct_format, self.encoding_size, self.aux_size, self.contents_size)


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
        aux_ofs = hsize + header.encoding_size
        contents_ofs = aux_ofs + header.aux_size
        contents_end = contents_ofs + header.contents_size
        encoding = data[hsize:aux_ofs]
        aux_data = data[aux_ofs:contents_ofs]
        contents = data[contents_ofs:contents_end]
        remainder = data[contents_end:]
        if aux_data:
            aux = packet_coders.decode(encoding, aux_data, tAuxInfo)
        else:
            aux = None
        return (cls(encoding, aux, contents), remainder)

    @classmethod
    def from_contents( cls, encoding, contents, t, aux=None ):
        data = packet_coders.encode(encoding, contents, t)
        return cls(encoding, aux, data)

    def __init__( self, encoding, aux, data ):
        assert isinstance(encoding, str), repr(encoding)
        if aux is not None:
            tAuxInfo.validate('AuxInfo', aux)
        assert isinstance(data, str), repr(data)
        self.encoding = encoding
        self.data = data
        self.aux = aux

    def __repr__( self ):
        return '%s packet: %d bytes, %s' % (self.encoding, len(self.data), 'with aux' if self.aux else 'without aux')

    def encode( self ):
        if self.aux:
            aux_data = packet_coders.encode(self.encoding, self.aux, tAuxInfo)
        else:
            aux_data = ''
        encoding_size = len(self.encoding)
        aux_size = len(aux_data)
        contents_size = len(self.data)
        return Header(encoding_size, aux_size, contents_size).encode() + self.encoding + aux_data + self.data

    def decode_server_packet( self, peer, iface_registry ):
        return decode_server_packet(peer, iface_registry, self.encoding, self.data)

    def decode_client_packet( self, peer, iface_registry ):
        return decode_client_packet(peer, iface_registry, self.encoding, self.data)
