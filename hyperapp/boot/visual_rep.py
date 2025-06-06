import codecs
import json
import logging
from functools import singledispatchmethod

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
    ref_t,
    capsule_t,
    )
from .util import encode_path, encode_route
from .htypes.deduce_value_type import deduce_value_type
from .ref import ref_repr, make_ref
from hyperapp.boot.type_repr import type_repr_registry

log = logging.getLogger(__name__)


class VisualRep:

    def __init__(self, t, value, name, text, children=None):
        self.t = t
        self.value = value
        self.name = name
        self.text = text
        self.children = children or []

    def pprint(self, logger, indent=0):
        logger("{}{}={}".format('  ' * indent, self.name, self.value))
        for node in self.children:
            node.pprint(logger, indent + 1)

    def dump(self, logger, indent=0):
        logger("{}{}: {} = {}".format('  ' * indent, self.name, self.t, self.value))
        for node in self.children:
            node.dump(logger, indent + 1)


def _value_repr(t, value):
    try:
        repr_fn = type_repr_registry[t]
    except KeyError:
        return repr(value)
    else:
        return repr_fn(value)


class VisualRepEncoder(object):

    def __init__(self):
        pass

    def encode(self, t, value, name=None):
        assert isinstance(value, t), repr(value)
        return self.dispatch(t, name or t.name, value)

    @singledispatchmethod
    def dispatch(self, t, name, value):
        assert False, repr((t, value))  # Unknown type

    @dispatch.register(TString)
    @dispatch.register(TInt)
    @dispatch.register(TBool)
    def encode_primitive(self, t, name, value):
        return VisualRep(t.name, value, name, _value_repr(t, value))

    @dispatch.register(TBinary)
    def encode_binary(self, t, name, value):
        return VisualRep(t.name, value, name, 'binary, len=%d: %s' % (len(value), codecs.encode(value[:40], 'hex')))

    @dispatch.register(TDateTime)
    def encode_datetime(self, t, name, value):
        return VisualRep(t.name, value, name, value.isoformat())

    @dispatch.register(TOptional)
    def encode_optional(self, t, name, value):
        if value is None:
            return VisualRep(t.name or "{} opt".format(t.base_t.name), value, name, value)
        return self.dispatch(t.base_t, name, value)

    @staticmethod
    def _make_name(t, type_name):
        if t.name:
            return '%s (%s)' % (t.name, type_name)
        else:
            return type_name

    @dispatch.register(TList)
    def encode_list(self, t, name, value):
        children = [self.dispatch(t.element_t, str(idx), elt)
                    for idx, elt in enumerate(value)]
        return VisualRep(t.name or "{} list".format(t.element_t.name), value, name, _value_repr(t, value), children)

    @dispatch.register(TRecord)
    def encode_record(self, t, name, value):
        children = self.encode_record_fields(t.fields, value)
        return VisualRep(t.name, value, name, _value_repr(t, value), children)

    def encode_record_fields(self, fields, value):
        return [self.dispatch(field_type, field_name, getattr(value, field_name))
                for field_name, field_type in fields.items()]


def pprint(value, t=None, indent=0, title=None, logger=log.info):
    t = t or deduce_value_type(value)
    rep = VisualRepEncoder().encode(t, value)
    if title:
        logger(title)
        indent += 1
    rep.pprint(logger, indent)
