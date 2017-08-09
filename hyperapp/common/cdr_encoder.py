import struct
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
    EncodableEmbedded,
    TEmbedded,
    THierarchy,
    )


class CdrEncoder(object):

    def encode(self, t, value):
        self.data = b''
        self.dispatch(t, value)
        return self.data

    @method_dispatch
    def dispatch(self, t, value):
        assert False, repr((t, value))  # Unknown type

    def write_int(self, value):
        self.data += struct.pack('!q', value)

    def write_bool(self, value):
        self.data += struct.pack('!?', value)

    def write_binary(self, value):
        assert isinstance(value, bytes), repr(value)
        self.write_int(len(value))
        self.data += value

    def write_unicode(self, value):
        if isinstance(value, str):
            value = value.encode('utf-8')
        self.write_int(len(value))
        self.data += value

    @dispatch.register(TInt)
    def encode_primitive(self, t, value):
        self.write_int(value)

    @dispatch.register(TBool)
    def encode_primitive(self, t, value):
        self.write_bool(value)

    @dispatch.register(TBinary)
    def encode_binary(self, t, value):
        self.write_binary(value)

    @dispatch.register(TString)
    def encode_primitive(self, t, value):
        self.write_unicode(value)

    @dispatch.register(TDateTime)
    def encode_datetime(self, t, value):
        self.write_unicode(value.isoformat())

    @dispatch.register(TOptional)
    def encode_optional(self, t, value):
        self.write_bool(value is not None)
        if value is not None:
            self.dispatch(t.base_t, value)

    @dispatch.register(TRecord)
    def encode_record(self, t, value):
        ## print '*** encoding record', value, t, [field.name for field in t.fields]
        for field in t.fields:
            self.dispatch(field.type, getattr(value, field.name))

    @dispatch.register(TList)
    def encode_list(self, t, value):
        self.write_int(len(value))
        for elt in value:
            self.dispatch(t.element_t, elt)

    @dispatch.register(TEmbedded)
    def encode_embedded(self, t, value):
        assert isinstance(value, EncodableEmbedded), repr(value)
        data = CdrEncoder().encode(value.type, value.value)
        self.dispatch(tBinary, data)

    @dispatch.register(THierarchy)
    def encode_hierarchy_obj(self, t, value):
        tclass = t.resolve_obj(value)
        self.write_unicode(tclass.id)
        self.dispatch(tclass.get_trecord(), value)
