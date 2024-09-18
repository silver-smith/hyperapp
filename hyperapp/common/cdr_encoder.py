import io
import struct
from functools import singledispatchmethod

from .htypes import (
    TNone,
    TString,
    TBinary,
    tBinary,
    TInt,
    TBool,
    TDateTime,
    tString,
    TOptional,
    TRecord,
    TException,
    TList,
    )


class CdrEncoder(object):

    _int_struct = struct.Struct('!q')
    _bool_struct = struct.Struct('!?')

    def encode(self, value, t):
        self._buf = io.BytesIO()
        self.dispatch(t, value)
        return self._buf.getvalue()

    @singledispatchmethod
    def dispatch(self, t, value):
        assert False, repr((t, value))  # Unknown type

    def write_int(self, value):
        self._buf.write(self._int_struct.pack(value))

    def write_bool(self, value):
        self._buf.write(self._bool_struct.pack(value))

    def write_binary(self, value):
        # assert isinstance(value, bytes), repr(value)
        self.write_int(len(value))
        self._buf.write(value)

    def write_unicode(self, value):
        if type(value) is not bytes:
            value = value.encode('utf-8')
        self.write_int(len(value))
        self._buf.write(value)

    @dispatch.register(TNone)
    def encode_none(self, t, value):
        pass

    @dispatch.register(TInt)
    def encode_int(self, t, value):
        self.write_int(value)

    @dispatch.register(TBool)
    def encode_bool(self, t, value):
        self.write_bool(value)

    @dispatch.register(TBinary)
    def encode_binary(self, t, value):
        self.write_binary(value)

    @dispatch.register(TString)
    def encode_string(self, t, value):
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
    @dispatch.register(TException)
    def encode_record(self, t, value):
        ## print '*** encoding record', value, t, [field.name for field in t.fields]
        for field_name, field_type in t.fields.items():
            self.dispatch(field_type, getattr(value, field_name))

    @dispatch.register(TList)
    def encode_list(self, t, value):
        self.write_int(len(value))
        for elt in value:
            self.dispatch(t.element_t, elt)
