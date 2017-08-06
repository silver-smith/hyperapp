import abc
import base64
import json
import yaml
from .method_dispatch import method_dispatch
from .htypes import (
    TString,
    TBinary,
    TInt,
    TBool,
    TDateTime,
    tString,
    TOptional,
    TRecord,
    TList,
    EncodableEmbedded,
    TEmbedded,
    TSwitchedRec,
    THierarchy,
    Interface,
    )


class DictEncoder(object, metaclass=abc.ABCMeta):

    def __init__(self, encoding):
        self._encoding = encoding

    def encode(self, t, value):
        return self._dict_to_str(self.dispatch(t, value)).encode()

    @abc.abstractmethod
    def _dict_to_str(self, value):
        pass

    @method_dispatch
    def dispatch(self, t, value):
        assert False, repr((t, value))  # Unknown type

    @dispatch.register(TString)
    @dispatch.register(TInt)
    @dispatch.register(TBool)
    def encode_primitive(self, t, value):
        return value

    @dispatch.register(TBinary)
    def encode_primitive(self, t, value):
        return str(base64.b64encode(value), 'ascii')

    @dispatch.register(TDateTime)
    def encode_datetime(self, t, value):
        return value.isoformat()

    @dispatch.register(TOptional)
    def encode_optional(self, t, value):
        if value is None:
            return None
        return self.dispatch(t.base_t, value)

    @dispatch.register(TRecord)
    def encode_record(self, t, value):
        fields = {}
        for field in t.get_fields():
            attr = getattr(value, field.name)
            fields[field.name] = self.dispatch(field.type, attr)
        return fields

    @dispatch.register(TList)
    def encode_list(self, t, value):
        return [self.dispatch(t.element_t, elt) for elt in value]

    @dispatch.register(TEmbedded)
    def encode_embedded(self, t, value):
        assert isinstance(value, EncodableEmbedded), repr(value)
        return self.dispatch(value.type, value.value)

    @dispatch.register(TSwitchedRec)
    def encode_switched_record(self, t, value):
        fields = {}
        for field in t.get_static_fields():
            attr = getattr(value, field.name)
            fields[field.name] = self.dispatch(field.type, attr)
        dyn_field = t.get_dynamic_field(fields)
        attr = getattr(value, dyn_field.name)
        fields[dyn_field.name] = self.dispatch(dyn_field.type, attr)
        return fields

    @dispatch.register(THierarchy)
    def encode_hierarchy_obj(self, t, value):
        tclass = t.resolve_obj(value)
        return dict(self.dispatch(tclass.get_trecord(), value),
                    _class_id=self.dispatch(tString, tclass.id))


class JsonEncoder(DictEncoder):

    def __init__(self, encoding, pretty=True):
        DictEncoder.__init__(self, encoding)
        self._pretty = pretty

    def _dict_to_str(self, value):
        return json.dumps(value, indent=4 if self._pretty else None)


class YamlEncoder(DictEncoder):

    def _dict_to_str(self, value):
        return yaml.dump(value)
