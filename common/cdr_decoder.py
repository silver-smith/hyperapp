import struct
import dateutil.parser
from .method_dispatch import method_dispatch
from . interface import (
    TString,
    TInt,
    TBool,
    TDateTime,
    tString,
    TOptional,
    TRecord,
    TDynamicRec,
    TList,
    TIndexedList,
    THierarchy,
    TObject,
    TIface,
    )


def join_path( *args ):
    return '.'.join(filter(None, args))


class DecodeError(Exception): pass


class CdrDecoder(object):

    def __init__( self, iface_registry ):
        self.iface_registry = iface_registry  # IfaceRegistry

    def decode( self, t, value, path='root' ):
        assert isinstance(value, str), repr(value)
        self.data = value
        self.ofs = 0
        return self.dispatch(t, path)

    def expect( self, path, expr, desc ):
        if not expr:
            self.failure(path, desc)

    def failure( self, path, desc ):
        raise DecodeError('%s: %s' % (path, desc))

    @method_dispatch
    def dispatch( self, t, path ):
        assert False, repr((t, path))  # Unknown type

    def read( self, size, path ):
        if self.ofs + size > len(self.data):
            raise DecodeError('%s: Unexpected EOF while reading %d bytes from ofs %d. Total size is %d'
                              % (path, size, self.ofs, len(self.data)))
        result = self.data[self.ofs : self.ofs + size]
        self.ofs += size
        return result
    
    def unpack( self, fmt, path ):
        fmt = '!' + fmt
        size = struct.calcsize(fmt)
        data = self.read(size, path)
        return struct.unpack(fmt, data)[0]

    def read_int( self, path ):
        return self.unpack('q', path)

    def read_bool( self, path ):
        return self.unpack('?', path)

    def read_str( self, path ):
        size = self.read_int(path)
        data = self.read(size, path)
        return data.decode('utf-8')

    @dispatch.register(TString)
    def decode_primitive( self, t, path ):
        return self.read_str(path)

    @dispatch.register(TInt)
    def decode_primitive( self, t, path ):
        return self.read_int(path)

    @dispatch.register(TBool)
    def decode_primitive( self, t, path ):
        return self.read_bool(path)

    @dispatch.register(TDateTime)
    def decode_datetime( self, t, path ):
        return dateutil.parser.parse(self.read_str(path))

    @dispatch.register(TOptional)
    def decode_optional( self, t, path ):
        value_present = self.read_bool(path)
        if value_present:
            return self.dispatch(t.type, path)
        else:
            return None

    @dispatch.register(TRecord)
    def decode_record( self, t, path ):
        base_fields = set()
        decoded_fields = {}
        while True:
            new_fields = [field for field in t.get_fields() if field.name not in base_fields]
            decoded_fields.update(self.decode_record_fields(new_fields, path))
            rec = t.instantiate_fixed(**decoded_fields)
            if not isinstance(t, TDynamicRec):
                return rec
            base_fields = set(field.name for field in t.get_fields())
            t = t.resolve_dynamic(rec)

    @dispatch.register(THierarchy)
    def decode_hierarchy_obj( self, t, path ):
        class_id = self.read_str(path)
        tclass = t.resolve(class_id)
        fields = self.decode_record_fields(tclass.get_fields(), path)
        return tclass.instantiate(**fields)

    def decode_record_fields( self, tfields, path ):
        fields = {}
        for field in tfields:
            elt = self.dispatch(field.type, join_path(path, field.name))
            fields[field.name] = elt
        return fields

    @dispatch.register(TList)
    def decode_list( self, t, path ):
        size = self.read_int(path)
        elements = []
        for idx in range(size):
            elt = self.dispatch(t.element_type, join_path(path, '#%d' % idx))
            elements.append(elt)
        return elements

    @dispatch.register(TIndexedList)
    def decode_indexed_list( self, t, path ):
        size = self.read_int(path)
        elements = []
        for idx in range(size):
            elt = self.dispatch(t.element_type, join_path(path, '#%d' % idx))
            setattr(elt, 'idx', idx)
            elements.append(elt)
        return elements

    @dispatch.register(TIface)
    def decode_iface( self, t, path ):
        iface_id = self.read_str(path)
        return self.iface_registry.resolve(iface_id)
