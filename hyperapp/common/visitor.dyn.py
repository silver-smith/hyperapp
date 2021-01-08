from hyperapp.common.method_dispatch import method_dispatch
from hyperapp.common.htypes import (
    TPrimitive,
    TOptional,
    TRecord,
    TEmbedded,
    THierarchy,
    TClass,
    TList,
    )


class Visitor(object):

    def visit(self, t, value):
        self.dispatch(t, value)

    def visit_primitive(self, t, value):
        pass

    def visit_record(self, t, value):
        pass

    def visit_hierarchy_obj(self, t, tclass, value):
        pass

    @method_dispatch
    def dispatch(self, t, value):
        assert False, repr((t, value))  # Unknown type

    @dispatch.register(TPrimitive)
    def process_primitive(self, t, value):
        self.visit_primitive(t, value)

    @dispatch.register(TOptional)
    def process_optional(self, t, value):
        if value is not None:
            self.dispatch(t.base_t, value)

    @dispatch.register(TRecord)
    def process_record(self, t, value):
        self.visit_record(t, value)
        fields = {}
        for field_name, field_type in t.fields.items():
            field_val = getattr(value, field_name)
            self.dispatch(field_type, field_val)
            fields[field_name] = field_val
            
    @dispatch.register(TEmbedded)
    def process_embedded(self, t, value):
        pass
            
    @dispatch.register(THierarchy)
    def process_hierarchy_obj(self, t, value):
        tclass = t.get_object_class(value)
        self.visit_hierarchy_obj(t, tclass, value)
        self.process_record(tclass, value)

    @dispatch.register(TClass)
    def process_tclass_obj(self, t, value):
        self.process_hierarchy_obj(t.hierarchy, value)

    def process_field(self, field, value):
        self.dispatch(field.type, getattr(value, field.name))

    @dispatch.register(TList)
    def process_list(self, t, value):
        for elt in value:
            self.dispatch(t.element_t, elt)
