from .method_dispatch import method_dispatch
from .interface import (
    TPrimitive,
    TOptional,
    TRecord,
    TSwitchedRec,
    THierarchy,
    TList,
    )


class Visitor(object):

    def visit( self, t, value ):
        self.dispatch(t, value)

    def visit_hierarchy_obj( self, t, tclass, value ):
        pass

    @method_dispatch
    def dispatch( self, t, value ):
        assert False, repr((t, value))  # Unknown type

    @dispatch.register(TPrimitive)
    def process_primitive( self, t, value ):
        pass

    @dispatch.register(TOptional)
    def process_optional( self, t, value ):
        if value is not None:
            self.dispatch(t.type, value)

    @dispatch.register(TRecord)
    def process_record( self, t, value ):
        fields = {}
        for field in t.get_static_fields():
            field_val = getattr(value, field.name)
            self.dispatch(field.type, field_val)
            fields[field.name] = field_val
        if isinstance(t, TSwitchedRec):
            field = t.get_dynamic_field(fields)
            self.dispatch(field.type, getattr(value, field.name))
            
    @dispatch.register(THierarchy)
    def process_hierarchy_obj( self, t, value ):
        tclass = t.resolve_obj(value)
        self.visit_hierarchy_obj(t, tclass, value)
        self.dispatch(tclass.get_trecord(), value)

    def process_field( self, field, value ):
        self.dispatch(field.type, getattr(value, field.name))

    @dispatch.register(TList)
    def process_list( self, t, value ):
        for elt in value:
            self.dispatch(t.element_type, elt)
