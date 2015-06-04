import dateutil.parser
from method_dispatch import method_dispatch
from interface.interface import (
    TString,
    TInt,
    TBool,
    TDateTime,
    TOptional,
    TRecord,
    TList,
    TRow,
    TPath,
    TObject,
    )


def join_path( *args ):
    return '.'.join(filter(None, args))


class Record(object): pass


class JsonDecoder(object):

    def __init__( self, iface_registry, handle_resolver ):
        self.iface_registry = iface_registry  # IfaceRegistry
        self.handle_resolver = handle_resolver  # obj info -> handle

    def decode( self, t, value, path=None ):
        t.validate(path, value)
        return self.dispatch(t, value, path)

    @method_dispatch
    def dispatch( self, t, value, path ):
        assert False, repr(t)  # Unknown type

    @dispatch.register(TString)
    @dispatch.register(TInt)
    @dispatch.register(TBool)
    def decode_primitive( self, t, value, path ):
        return value

    @dispatch.register(TDateTime)
    def decode_datetime( self, t, value, path ):
        assert isinstance(value, basestring), repr(value)
        return dateutil.parser.parse(value)

    @dispatch.register(TOptional)
    def decode_optional( self, t, value, path ):
        if value is None:
            return None
        return self.dispatch(t.type, value, path)

    @dispatch.register(TRecord)
    def decode_record( self, t, value, path ):
        rec = Record()
        for field in t.fields:
            elt = self.dispatch(field.type, value[field.name], join_path(path, field.name))
            setattr(rec, field.name, elt)
        return rec

    @dispatch.register(TList)
    def decode_list( self, t, value, path ):
        return [self.dispatch(t.element_type, elt, join_path(path, '#%d' % idx))
                for idx, elt in enumerate(value)]

    @dispatch.register(TRow)
    def decode_row( self, t, value, path ):
        result = []
        for idx, t in enumerate(t.columns):
            result.append(self.dispatch(t, value[idx], join_path(path, '#%d' % idx)))
        return result

    @dispatch.register(TPath)
    def decode_path( self, t, value, path ):
        return path

    @dispatch.register(TObject)
    def decode_object( self, t, value, path ):
        info = self.decode_record(t, value, path)
        iface = self.iface_registry.resolve(info.iface_id)
        iface.validate_contents(info.contents)
        return self.handle_resolver(info)
