import abc
import base64
import codecs
import json
from functools import singledispatchmethod

import yaml
import dateutil.parser

from .htypes import (
    TNone,
    TString,
    TBinary,
    TInt,
    TBool,
    TDateTime,
    tString,
    TOptional,
    TRecord,
    TException,
    TList,
    ref_t,
    )
from .htypes.packet_coders import DecodeError
from .named_pairs_coder import is_named_pair_list_t


def join_path(*args):
    return '.'.join([_f for _f in args if _f])


class DictDecoder(metaclass=abc.ABCMeta):

    def __init__(self, mosaic=None, types=None):
        self._mosaic = mosaic
        self._types = types

    def decode_dict(self, t, value, path='root'):
        return self.dispatch(t, value, path)

    def expect(self, path, expr, desc):
        if not expr:
            self.failure(path, desc)

    def expect_type(self, path, expr, value, type_name):
        if not expr:
            self.failure(path, '%s is expected, but got: %r' % (type_name, value))

    def failure(self, path, desc):
        raise DecodeError('%s: %s' % (path, desc))

    @singledispatchmethod
    def dispatch(self, t, value, path):
        assert False, repr((t, path, value))  # Unknown type

    @dispatch.register(TNone)
    def decode_none(self, t, value, path):
        self.expect_type(path, value is None, value, 'none')
        return None

    @dispatch.register(TString)
    def decode_string(self, t, value, path):
        self.expect_type(path, isinstance(value, str), value, 'string')
        return value

    @dispatch.register(TBinary)
    def decode_binary(self, t, value, path):
        self.expect_type(path, isinstance(value, str), value, 'string')
        return base64.b64decode(value)

    @dispatch.register(TInt)
    def decode_int(self, t, value, path):
        self.expect_type(path, isinstance(value, int), value, 'integer')
        return value

    @dispatch.register(TBool)
    def decode_bool(self, t, value, path):
        self.expect_type(path, isinstance(value, bool), value, 'bool')
        return value

    @dispatch.register(TDateTime)
    def decode_datetime(self, t, value, path):
        self.expect_type(path, isinstance(value, str), value, 'datetime (string)')
        return dateutil.parser.parse(value)

    @dispatch.register(TOptional)
    def decode_optional(self, t, value, path):
        if value is None:
            return None
        return self.dispatch(t.base_t, value, path)

    @dispatch.register(TRecord)
    @dispatch.register(TException)
    def decode_record(self, t, value, path):
        if t is ref_t and self._mosaic:
            return self._decode_ref(value, path)
        return self._decode_record_impl(t, value, path)

    def _decode_record_impl(self, t, value, path):
        self.expect_type(path, isinstance(value, dict), value, 'record (dict)')
        fields = self.decode_record_fields(t.fields, value, path)
        return t(**fields)

    @dispatch.register(TList)
    def _decode_list(self, t, value, path):
        return self.decode_list(t, value, path)

    def decode_list(self, t, value, path):
        self.expect_type(path, isinstance(value, list), value, 'list')
        return tuple(self.dispatch(t.element_t, elt, join_path(path, '#%d' % idx))
                     for idx, elt in enumerate(value))

    def decode_record_fields(self, fields, value, path):
        decoded_fields = {}
        for field_name, field_type in fields.items():
            if field_name in value:
                elt = self.dispatch(field_type, value[field_name], join_path(path, field_name))
                decoded_fields[field_name] = elt
            elif not isinstance(field_type, TOptional):
                self.failure(path, 'field %r is missing' % field_name)
        return decoded_fields

    def _decode_ref(self, value, path):
        hash_algorithm, hash_str = value['type_ref'].split(':', 1)
        hash = codecs.decode(hash_str, 'hex')
        type_ref = ref_t(hash_algorithm, hash)
        t = self._types.resolve(type_ref)
        value = self.dispatch(t, value['value'], join_path(path, 'value'))
        ref = self._mosaic.put(value, t)
        return ref


class NamedPairsDictDecoder(DictDecoder):

    def decode_list(self, t, value, path):
        if type(value) is dict and is_named_pair_list_t(t):
            return self._decode_named_pair_list(t.element_t, value, path)
        return super().decode_list(t, value, path)

    def _decode_named_pair_list(self, element_t, list_value, path):
        key_t, value_t = element_t.fields.values()
        result = []
        for idx, (key, raw_value) in enumerate(list_value.items()):
            value = self.dispatch(value_t, raw_value, join_path(path, f'#{idx}', 'value'))
            result.append(element_t(key, value))
        return tuple(result)

class DictDecoderBase(DictDecoder, metaclass=abc.ABCMeta):

    def decode(self, t, value, path='root'):
        assert isinstance(value, bytes), repr(value)
        return self.decode_dict(t, self._str_to_dict(value.decode()), path)

    @abc.abstractmethod
    def _str_to_dict(self, value):
        pass


class JsonDecoder(DictDecoderBase):

    def _str_to_dict(self, value):
        try:
            return json.loads(value)
        except json.JSONDecodeError as x:
            raise DecodeError(str(x)) from x


class YamlDecoder(DictDecoderBase):

    def _str_to_dict(self, value):
        return yaml.safe_load(value)
