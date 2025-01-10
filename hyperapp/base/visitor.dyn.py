from functools import singledispatchmethod

from hyperapp.common.htypes import (
    TPrimitive,
    TOptional,
    TRecord,
    TException,
    TList,
    )


class Visitor:

    def visit(self, t, value):
        self.dispatch(t, value)

    def visit_primitive(self, t, value):
        pass

    def visit_record(self, t, value):
        pass

    @singledispatchmethod
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
    @dispatch.register(TException)
    def process_record(self, t, value):
        self.visit_record(t, value)
        fields = {}
        for field_name, field_type in t.fields.items():
            field_val = getattr(value, field_name)
            self.dispatch(field_type, field_val)
            fields[field_name] = field_val
            
    @dispatch.register(TList)
    def process_list(self, t, value):
        for elt in value:
            self.dispatch(t.element_t, elt)
