import struct
from functools import singledispatchmethod

import dateutil.parser

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
    TList,
    TRecord,
    TException,
    TRef,
    )
from .htypes.packet_coders import DecodeError


MAX_SANE_LIST_SIZE = 1 << 60


class DecodeBuffer:

    _int_struct = struct.Struct('!q')
    _bool_struct = struct.Struct('!?')

    def __init__(self, data):
        self._data = data
        self._ofs = 0

    def read(self, size, path):
        if self._ofs + size > len(self._data):
            path_str = ".".join(path)
            raise DecodeError(
                f"{path_str}: Unexpected EOF while reading {size} bytes from ofs {self._ofs}."
                f" Total size is {len(self._data)}"
                )
        result = self._data[self._ofs : self._ofs + size]
        self._ofs += size
        return result

    def _unpack(self, st, path):
        data = self.read(st.size, path)
        return st.unpack(data)[0]

    def read_int(self, path):
        return self._unpack(self._int_struct, path)

    def read_bool(self, path):
        return self._unpack(self._bool_struct, path)

    def read_binary(self, path):
        size = self.read_int(path)
        return self.read(size, path)

    def read_unicode(self, path):
        data = self.read_binary(path)
        return data.decode('utf-8')


def join_path(*args):
    return '.'.join([_f for _f in args if _f])


def _decode_none(buf, path):
    return None


def _decode_binary(buf, path):
    return buf.read_binary(path)


def _decode_string(buf, path):
    return buf.read_unicode(path)


def _decode_int(buf, path):
    return buf.read_int(path)


def _decode_bool(buf, path):
    return buf.read_bool(path)


def _decode_datetime(buf, path):
    return dateutil.parser.parse(buf.read_unicode(path))


class OptionalDecoder:

    @classmethod
    def construct(cls, t):
        base_decoder = _type_to_decoder(t.base_t)
        return cls(base_decoder)

    def __init__(self, base_decoder):
        self._base_decoder = base_decoder

    def __call__(self, buf, path):
        value_present = buf.read_bool(path)
        if value_present:
            return self._base_decoder(buf, path)
        else:
            return None


class ListDecoder:

    @classmethod
    def construct(cls, t):
        elt_decoder = _type_to_decoder(t.element_t)
        return cls(elt_decoder)

    def __init__(self, elt_decoder):
        self._elt_decoder = elt_decoder

    def __call__(self, buf, path):
        size = buf.read_int(path)
        if size > MAX_SANE_LIST_SIZE:
            path_str = ".".join(path)
            raise DecodeError(f"{path_str}: List size is too large: {size}")
        return tuple(
            self._elt_decoder(buf, [*path, f"#{idx}"])
            for idx in range(size)
            )


class RecordDecoder:

    @classmethod
    def construct(cls, t):
        field_to_decoder = {
            name: _type_to_decoder(field_t)
            for name, field_t in t.fields.items()
            }
        return cls(t, field_to_decoder)

    def __init__(self, t, field_to_decoder):
        self._t = t
        self._field_to_decoder = field_to_decoder

    def __call__(self, buf, path):
        fields = {
            name: decoder(buf, [*path, name])
            for name, decoder in self._field_to_decoder.items()
            }
        return self._t(**fields)


_type_to_primitive_decoder = {
    TNone: _decode_none,
    TBinary: _decode_binary,
    TString: _decode_string,
    TInt: _decode_int,
    TBool: _decode_bool,
    TDateTime: _decode_datetime,
    }

_type_to_decoder_ctr = {
    TOptional: OptionalDecoder.construct,
    TList: ListDecoder.construct,
    TRecord: RecordDecoder.construct,
    TException: RecordDecoder.construct,
    TRef: RecordDecoder.construct,
    }


# Global cache, persists between systems, so elements are accumulated with time.
# TODO: May be improve by using weak key dict or LRU eviction.
_type_to_decoder_cache = {}


def _type_to_decoder(t):
    try:
        return _type_to_decoder_cache[t]
    except KeyError:
        pass
    tt = type(t)
    try:
        decoder = _type_to_primitive_decoder[tt]
    except KeyError:
        ctr = _type_to_decoder_ctr[tt]
        decoder = ctr(t)
    _type_to_decoder_cache[t] = decoder
    return decoder


class CdrDecoder:

    @staticmethod
    def decode(t, value):
        decoder = _type_to_decoder(t)
        buf = DecodeBuffer(value)
        return decoder(buf, path=[])
