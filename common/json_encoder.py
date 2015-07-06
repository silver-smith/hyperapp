import json
from method_dispatch import method_dispatch
from . interface import (
    TString,
    TInt,
    TBool,
    TDateTime,
    TOptional,
    TRecord,
    TList,
    TRow,
    TPath,
    TDynamicRec,
    TUpdate,
    Object,
    TObject,
    Interface,
    TIface,
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
        ## print '*** encoding record', t, value
        result = {}
        while True:
            ## print '  * encoding', t
            for field in t.get_fields():
                result[field.name] = self.dispatch(field.type, getattr(value, field.name))
            if not isinstance(t, TDynamicRec): break
            t = t.resolve_rec(value)
        ## print '  >', result
        return result

    @dispatch.register(TList)
    def encode_list( self, t, value ):
        return [self.dispatch(t.element_type, elt) for elt in value]

    @dispatch.register(TRow)
    def encode_row( self, t, value ):
        result = []
        for idx, t in enumerate(t.columns):
            result.append(self.dispatch(t, value[idx]))
        return result

    @dispatch.register(TPath)
    def encode_path( self, t, value ):
        return value

    @dispatch.register(TUpdate)
    def encode_update( self, t, value ):
        iface = value.iface
        info = self.dispatch(t.info_type, value)
        return dict(info,
                    diff=self.dispatch(iface.tDiff(), value.diff))

    @dispatch.register(TObject)
    def encode_object( self, t, obj ):
        assert isinstance(obj, Object), repr(obj)
        return self.dispatch(obj.iface.get_type(), obj.get())

    @dispatch.register(TIface)
    def encode_iface( self, t, obj ):
        assert isinstance(obj, Interface), repr(obj)
        return obj.iface_id
