import json
from method_dispatch import method_dispatch
from interface.types import (
    TString,
    TInt,
    TBool,
    TDateTime,
    TOptional,
    TRecord,
    TList,
    TRow,
    TColumnType,
    TPath,
    TUpdate,
    Object,
    TObject,
    )
from request import Update


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
    def encode_record( self, t, value, **kw ):
        result = {}
        for field in t.fields:
            result[field.name] = self.dispatch(field.type, value[field.name])
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

    @dispatch.register(TColumnType)
    def encode_column_type( self, t, value ):
        return value.id

    @dispatch.register(TPath)
    def encode_path( self, t, value ):
        return value

    @dispatch.register(TUpdate)
    def encode_update( self, t, value ):
        assert isinstance(value, Update), repr(value)
        iface = value.iface
        info = self.dispatch(t.info_type, dict(iface_id=iface.iface_id,
                                               path=value.path))
        return dict(info,
                    diff=self.dispatch(iface.get_update_type(), value.diff))

    @dispatch.register(TObject)
    def encode_object( self, t, obj ):
        assert isinstance(obj, Object), repr(obj)
        return self.dispatch(obj.iface.get_type(), obj.get())
