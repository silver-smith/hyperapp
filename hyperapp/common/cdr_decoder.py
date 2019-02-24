import struct
import dateutil.parser
from .method_dispatch import method_dispatch
from .htypes import (
    TString,
    TBinary,
    tBinary,
    TInt,
    TBool,
    TDateTime,
    tString,
    TOptional,
    TRecord,
    TList,
    TIndexedList,
    DecodableEmbedded,
    TEmbedded,
    THierarchy,
    TClass,
    )
from .htypes.packet_coders import DecodeError


MAX_SANE_LIST_SIZE = 1 << 60


def join_path(*args):
    return '.'.join([_f for _f in args if _f])


class CdrDecodableEmbedded(DecodableEmbedded):

    def decode(self, t):
        return CdrDecoder().decode(t, self.data, path='embedded')


class CdrDecoder(object):

    def decode(self, t, value, path='root'):
        assert isinstance(value, bytes), repr(value)
        self.data = value
        self.ofs = 0
        return self.dispatch(t, path)

    def expect(self, path, expr, desc):
        if not expr:
            self.failure(path, desc)

    def failure(self, path, desc):
        raise DecodeError('%s: %s' % (path, desc))

    @method_dispatch
    def dispatch(self, t, path):
        assert False, repr((t, path))  # Unknown type

    def read(self, size, path):
        if self.ofs + size > len(self.data):
            raise DecodeError('%s: Unexpected EOF while reading %d bytes from ofs %d. Total size is %d'
                              % (path, size, self.ofs, len(self.data)))
        result = self.data[self.ofs : self.ofs + size]
        self.ofs += size
        return result
    
    def unpack(self, fmt, path):
        fmt = '!' + fmt
        size = struct.calcsize(fmt)
        data = self.read(size, path)
        return struct.unpack(fmt, data)[0]

    def read_int(self, path):
        return self.unpack('q', path)

    def read_bool(self, path):
        return self.unpack('?', path)

    def read_binary(self, path):
        size = self.read_int(path)
        data = self.read(size, path)
        return data

    def read_unicode(self, path):
        size = self.read_int(path)
        data = self.read(size, path)
        return data.decode('utf-8')

    @dispatch.register(TBinary)
    def decode_primitive(self, t, path):
        return self.read_binary(path)

    @dispatch.register(TString)
    def decode_primitive(self, t, path):
        return self.read_unicode(path)

    @dispatch.register(TInt)
    def decode_primitive(self, t, path):
        return self.read_int(path)

    @dispatch.register(TBool)
    def decode_primitive(self, t, path):
        return self.read_bool(path)

    @dispatch.register(TDateTime)
    def decode_datetime(self, t, path):
        return dateutil.parser.parse(self.read_unicode(path))

    @dispatch.register(TOptional)
    def decode_optional(self, t, path):
        value_present = self.read_bool(path)
        if value_present:
            return self.dispatch(t.base_t, path)
        else:
            return None

    @dispatch.register(TRecord)
    def decode_record(self, t, path):
        fields = self.decode_record_fields(t.fields, path)
        return t(**fields)

    def decode_record_fields(self, fields, path):
        decoded_fields = {}
        for field in fields:
            elt = self.dispatch(field.type, join_path(path, field.name))
            decoded_fields[field.name] = elt
        return decoded_fields

    @dispatch.register(TList)
    def decode_list(self, t, path):
        size = self.read_int(path)
        elements = []
        if size > MAX_SANE_LIST_SIZE:
            raise DecodeError('List size is too large: %d' % size)
        for idx in range(size):
            elt = self.dispatch(t.element_t, join_path(path, '#%d' % idx))
            elements.append(elt)
        return elements

    @dispatch.register(TIndexedList)
    def decode_indexed_list(self, t, path):
        size = self.read_int(path)
        elements = []
        for idx in range(size):
            elt = self.dispatch(t.element_t, join_path(path, '#%d' % idx))
            setattr(elt, 'idx', idx)
            elements.append(elt)
        return elements

    @dispatch.register(TEmbedded)
    def decode_embedded(self, t, path):
        data = self.dispatch(tBinary, path)
        return CdrDecodableEmbedded(data)
        
    @dispatch.register(THierarchy)
    def decode_hierarchy_obj(self, t, path):
        class_id = self.read_unicode(path)
        tclass = t.resolve(class_id)
        fields = self.decode_record_fields(tclass.fields, path)
        return tclass(**fields)

    @dispatch.register(TClass)
    def decode_tclass_obj(self, t, path):
        return self.decode_hierarchy_obj(t.hierarchy, path)
