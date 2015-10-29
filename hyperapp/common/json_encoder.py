import json
from .method_dispatch import method_dispatch
from .interface import (
    TString,
    TInt,
    TBool,
    TDateTime,
    tString,
    TOptional,
    TRecord,
    TList,
    TSwitchedRec,
    THierarchy,
    Interface,
    )


class JsonEncoder(object):

    def encode( self, t, value ):
        return json.dumps(self.dispatch(t, value))

    @method_dispatch
    def dispatch( self, t, value ):
        assert False, repr((t, value))  # Unknown type

    @dispatch.register(TString)
    @dispatch.register(TInt)
    @dispatch.register(TBool)
    def encode_primitive( self, t, value ):
        return value

    @dispatch.register(TDateTime)
    def encode_datetime( self, t, value ):
        return value.isoformat()

    @dispatch.register(TOptional)
    def encode_optional( self, t, value ):
        if value is None:
            return None
        return self.dispatch(t.type, value)

    @dispatch.register(TRecord)
    def encode_record( self, t, value ):
        fields = {}
        for field in t.get_fields():
            attr = getattr(value, field.name)
            fields[field.name] = self.dispatch(field.type, attr)
        return fields

    @dispatch.register(TSwitchedRec)
    def encode_switched_record( self, t, value ):
        fields = {}
        for field in t.get_static_fields():
            attr = getattr(value, field.name)
            fields[field.name] = self.dispatch(field.type, attr)
        dyn_field = t.get_dynamic_field(fields)
        attr = getattr(value, dyn_field.name)
        fields[dyn_field.name] = self.dispatch(dyn_field.type, attr)
        return fields

    @dispatch.register(THierarchy)
    def encode_hierarchy_obj( self, t, value ):
        tclass = t.resolve_obj(value)
        return dict(self.dispatch(tclass.get_trecord(), value),
                    _class_id=self.dispatch(tString, tclass.id))

    @dispatch.register(TList)
    def encode_list( self, t, value ):
        return [self.dispatch(t.element_type, elt) for elt in value]
