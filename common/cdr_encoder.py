import struct
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
    THierarchy,
    Object,
    TObject,
    Interface,
    TIface,
    )


class CdrEncoder(object):

    def encode( self, t, value ):
        self.data = ''
        self.dispatch(t, value)
        return self.data

    @method_dispatch
    def dispatch( self, t, value ):
        assert False, repr((t, value))  # Unknown type

    def write_int( self, value ):
        self.data += struct.pack('!q', value)

    def write_bool( self, value ):
        self.data += struct.pack('!?', value)

    def write_str( self, value ):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        self.write_int(len(value))
        self.data += value

    @dispatch.register(TInt)
    def encode_primitive( self, t, value ):
        self.write_int(value)

    @dispatch.register(TBool)
    def encode_primitive( self, t, value ):
        self.write_bool(value)

    @dispatch.register(TString)
    def encode_primitive( self, t, value ):
        self.write_str(value)

    @dispatch.register(TDateTime)
    def encode_datetime( self, t, value ):
        self.write_str(value.isoformat())

    @dispatch.register(TOptional)
    def encode_optional( self, t, value ):
        self.write_bool(value is not None)
        if value is not None:
            return self.dispatch(t.type, value)

    @dispatch.register(TRecord)
    def encode_record( self, t, value ):
        ## print '*** encoding record', value, t, [field.name for field in t.get_fields()]
        base_fields = set()
        while True:
            new_fields = [field for field in t.get_fields() if field.name not in base_fields]
            for field in new_fields:
                self.dispatch(field.type, getattr(value, field.name))
            if not isinstance(t, TDynamicRec):
                break
            base_fields = set(field.name for field in t.get_fields())
            t = t.resolve_dynamic(value)

    @dispatch.register(THierarchy)
    def encode_hierarchy_obj( self, t, value ):
        tclass = t.resolve_obj(value)
        self.write_str(tclass.id)
        for field in tclass.get_fields():
            self.dispatch(field.type, getattr(value, field.name))

    @dispatch.register(TList)
    def encode_list( self, t, value ):
        self.write_int(len(value))
        for elt in value:
            self.dispatch(t.element_type, elt)

    @dispatch.register(TIface)
    def encode_iface( self, t, obj ):
        assert isinstance(obj, Interface), repr(obj)
        self.write_str(obj.iface_id)
