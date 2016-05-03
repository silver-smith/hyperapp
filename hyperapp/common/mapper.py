from .method_dispatch import method_dispatch
from .htypes import (
    TPrimitive,
    TOptional,
    TRecord,
    TSwitchedRec,
    THierarchy,
    TList,
    )


class Mapper(object):

    def map( self, t, value ):
        return self.dispatch(t, value)

    def map_hierarchy_obj( self, tclass, value ):
        return value

    @method_dispatch
    def dispatch( self, t, value ):
        assert False, repr((t, value))  # Unknown type

    @dispatch.register(TPrimitive)
    def process_primitive( self, t, value ):
        return value

    @dispatch.register(TOptional)
    def process_optional( self, t, value ):
        if value is None:
            return None
        else:
            return self.dispatch(t.type, value)

    @dispatch.register(TList)
    def process_list( self, t, value ):
        return [self.dispatch(t.element_type, elt) for elt in value]

    @dispatch.register(TRecord)
    def process_record( self, t, value ):
        fields = self.map_record_fields(t, value)
        return t(**fields)
            
    @dispatch.register(THierarchy)
    def process_hierarchy_obj( self, t, value ):
        tclass = t.resolve_obj(value)
        fields = self.map_record_fields(tclass.get_trecord(), value)
        mapped_obj = tclass(**fields)
        return self.map_hierarchy_obj(tclass, mapped_obj)

    def map_record_fields( self, t, value ):
        fields = {}
        mapped_fields = {}
        for field in t.get_static_fields():
            field_val = getattr(value, field.name)
            mapped_val = self.dispatch(field.type, field_val)
            fields[field.name] = field_val
            mapped_fields[field.name] = mapped_val
        if isinstance(t, TSwitchedRec):
            field = t.get_dynamic_field(fields)
            mapped_val = self.dispatch(field.type, getattr(value, field.name))
            mapped_fields[field.name] = mapped_val
        return mapped_fields
