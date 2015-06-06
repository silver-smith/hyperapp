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


class DecodeError(Exception): pass
class Record(object): pass


class JsonDecoder(object):

    def __init__( self, iface_registry, handle_resolver=None ):
        self.iface_registry = iface_registry  # IfaceRegistry
        self.handle_resolver = handle_resolver  # obj info -> handle

    def decode( self, t, value, path='root' ):
        return self.dispatch(t, value, path)

    def expect( self, path, expr, desc ):
        if not expr:
            self.failure(path, desc)

    def expect_type( self, path, expr, value, type_name ):
        if not expr:
            self.failure(path, '%s is expected, but got: %r' % (type_name, value))

    def failure( self, path, desc ):
        raise DecodeError('%s: %s' % (path, desc))

    @method_dispatch
    def dispatch( self, t, value, path ):
        assert False, repr((t, path, value))  # Unknown type

    @dispatch.register(TString)
    def decode_primitive( self, t, value, path ):
        self.expect_type(path, isinstance(value, basestring), value, 'string')
        return value

    @dispatch.register(TInt)
    def decode_primitive( self, t, value, path ):
        self.expect_type(path, isinstance(value, (int, long)), value, 'integer')
        return value

    @dispatch.register(TBool)
    def decode_primitive( self, t, value, path ):
        self.expect_type(path, isinstance(value, bool), value, 'bool')
        return value

    @dispatch.register(TDateTime)
    def decode_datetime( self, t, value, path ):
        self.expect_type(path, isinstance(value, basestring), value, 'datetime (string)')
        return dateutil.parser.parse(value)

    @dispatch.register(TOptional)
    def decode_optional( self, t, value, path ):
        if value is None:
            return None
        return self.dispatch(t.type, value, path)

    @dispatch.register(TRecord)
    def decode_record( self, t, value, path, **kw ):
        self.expect_type(path, isinstance(value, dict), value, 'record (dict)')
        rec = Record()
        for field in t.fields:
            self.expect(path, field.name in value, 'field %r is missing' % field.name)
            if field.type is not None:
                field_type = field.type
            else:  # open type
                field_type = kw[field.name]  # must be passed explicitly
            elt = self.dispatch(field_type, value[field.name], join_path(path, field.name))
            setattr(rec, field.name, elt)
        return rec

    @dispatch.register(TList)
    def decode_list( self, t, value, path ):
        self.expect_type(path, isinstance(value, list), value, 'list')
        return [self.dispatch(t.element_type, elt, join_path(path, '#%d' % idx))
                for idx, elt in enumerate(value)]

    @dispatch.register(TRow)
    def decode_row( self, t, value, path ):
        self.expect_type(path, isinstance(value, list), value, 'row (list)')
        result = []
        for idx, t in enumerate(t.columns):
            result.append(self.dispatch(t, value[idx], join_path(path, '#%d' % idx)))
        return result

    @dispatch.register(TPath)
    def decode_path( self, t, value, path ):
        self.expect_type(path, isinstance(value, dict), value, 'path (dict)')
        return value

    @dispatch.register(TObject)
    def decode_object( self, t, value, path ):
        assert self.handle_resolver  # object decoding is not supported
        self.expect_type(path, isinstance(value, dict), value, 'object (dict)')
        self.expect(path, 'iface_id' in value, 'iface_id field is missing')
        iface = self.iface_registry.resolve(value['iface_id'])
        objinfo = self.decode_record(t, value, path, contents=iface.get_contents_type())
        return self.handle_resolver(objinfo)
