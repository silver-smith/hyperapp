from .method_dispatch import method_dispatch
from .htypes import (
    TPrimitive,
    TOptional,
    TRecord,
    THierarchy,
    TList,
    )
from .htypes.deduce_value_type import deduce_value_type


class Mapper(object):

    def map(self, value, t=None):
        t = t or deduce_value_type(value)
        return self.dispatch(t, value)

    def map_hierarchy_obj(self, tclass, value):
        return value

    @method_dispatch
    def dispatch(self, t, value):
        assert False, repr((t, value))  # Unknown type

    @dispatch.register(TPrimitive)
    def process_primitive(self, t, value):
        return value

    @dispatch.register(TOptional)
    def process_optional(self, t, value):
        if value is None:
            return None
        else:
            return self.dispatch(t.base_t, value)

    @dispatch.register(TList)
    def process_list(self, t, value):
        return [self.dispatch(t.element_t, elt) for elt in value]

    @dispatch.register(TRecord)
    def process_record(self, t, value):
        fields = self.map_record_fields(t, value)
        return t(**fields)
            
    @dispatch.register(THierarchy)
    def process_hierarchy_obj(self, t, value):
        tclass = t.get_object_class(value)
        fields = self.map_record_fields(tclass, value)
        mapped_obj = tclass(**fields)
        return self.map_hierarchy_obj(tclass, mapped_obj)

    def map_record_fields(self, t, value):
        mapped_fields = {}
        for field_name, field_type in t.fields.items():
            field_val = getattr(value, field_name)
            mapped_val = self.dispatch(field_type, field_val)
            mapped_fields[field_name] = mapped_val
        return mapped_fields
