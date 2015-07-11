import struct
from method_dispatch import method_dispatch
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
    TRow,
    THierarchy,
    Object,
    TObject,
    Interface,
    TIface,
    )


class OStream(object):

    def __init__( self ):
        self.data = ''

    def get_result( self ):
        return self.data

    def write( self, data ):
        self.data += data

        
class CdrEncoder(object):

    def encode( self, t, value ):
        os = OStream()
        self.dispatch(t, value, os)
        return os.get_result()

    @method_dispatch
    def dispatch( self, t, value, os ):
        assert False, repr((t, value))  # Unknown type

    def write_int( self, value, os ):
        os.write(struct.pack('!q', value))

    def write_bool( self, value, os ):
        os.write(struct.pack('!?', value))

    def write_str( self, value, os ):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        self.write_int(len(value), os)
        os.write(value)

    @dispatch.register(TInt)
    def encode_primitive( self, t, value, os ):
        self.write_int(value, os)

    @dispatch.register(TBool)
    def encode_primitive( self, t, value, os ):
        self.write_bool(value, os)

    @dispatch.register(TString)
    def encode_primitive( self, t, value, os ):
        self.write_str(value, os)

    @dispatch.register(TDateTime)
    def encode_datetime( self, t, value, os ):
        self.write_str(value.isoformat(), os)

    @dispatch.register(TOptional)
    def encode_optional( self, t, value, os ):
        self.write_bool(value is not None)
        if value is not None:
            return self.dispatch(t.type, value, os)

    @dispatch.register(TRecord)
    def encode_record( self, t, value, os ):
        ## print '*** encoding record', value, t, [field.name for field in t.get_fields()]
        base_fields = set()
        while True:
            new_fields = [field for field in t.get_fields() if field.name not in base_fields]
            for field in new_fields:
                self.dispatch(field.type, getattr(value, field.name), os)
            if not isinstance(t, TDynamicRec):
                break
            base_fields = set(field.name for field in t.get_fields())
            t = t.resolve_dynamic(value)

    @dispatch.register(THierarchy)
    def encode_hierarchy_obj( self, t, value, os ):
        tclass = t.resolve_obj(value)
        self.write_str(tclass.id)
        for field in tclass.get_fields():
            self.dispatch(field.type, getattr(value, field.name), os)
        return result

    @dispatch.register(TList)
    def encode_list( self, t, value, os ):
        self.write_int(len(value), os)
        for elt in value:
            self.dispatch(t.element_type, elt, os)

    @dispatch.register(TRow)
    def encode_row( self, t, value, os ):
        assert len(value) == len(t.columns), repr(value)
        self.write_int(len(value), os)
        for t, elt in zip(t.columns, value):
            self.dispatch(t, elt, os)

    @dispatch.register(TObject)
    def encode_object( self, t, obj, os ):
        assert isinstance(obj, Object), repr(obj)
        self.encode_record(t, obj.get(), os)

    @dispatch.register(TIface)
    def encode_iface( self, t, obj, os ):
        assert isinstance(obj, Interface), repr(obj)
        self.write_str(obj.iface_id, os)
