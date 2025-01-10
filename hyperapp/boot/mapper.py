from functools import singledispatchmethod

from .htypes import (
    TPrimitive,
    TOptional,
    TRecord,
    TList,
    )
from .htypes.deduce_value_type import deduce_value_type


class Mapper(object):

    def map(self, value, t=None, context=None):
        if t is None:
            t = deduce_value_type(value)
        return self.dispatch(t, value, context)

    def map_record(self, t, value, context):
        return value

    @singledispatchmethod
    def dispatch(self, t, value, context):
        assert False, repr((t, value))  # Unknown type

    @dispatch.register(TPrimitive)
    def _process_primitive(self, t, value, context):
        return self.process_primitive(t, value, context)

    def process_primitive(self, t, value, context):
        return value

    @dispatch.register(TOptional)
    def process_optional(self, t, value, context):
        if value is None:
            return None
        else:
            return self.dispatch(t.base_t, value, context)

    @dispatch.register(TList)
    def process_list(self, t, value, context):
        return tuple(self.dispatch(t.element_t, elt, context) for elt in value)

    @dispatch.register(TRecord)
    def _process_record(self, t, value, context):
        return self.process_record(t, value, context)

    def process_record(self, t, value, context):
        fields = self.map_record_fields(t, value, context)
        result = t(**fields)
        return self.map_record(t, result, context)
            
    def map_record_fields(self, t, value, context):
        mapped_fields = {}
        for field_name, field_type in t.fields.items():
            field_value = getattr(value, field_name)
            field_context = self.field_context(context, field_name, field_value)
            mapped_value = self.dispatch(field_type, field_value, field_context)
            mapped_fields[field_name] = mapped_value
        return mapped_fields

    def field_context(self, context, name, value):
        return context
