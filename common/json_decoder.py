import dateutil.parser
from method_dispatch import method_dispatch
from . interface import (
    TString,
    TInt,
    TBool,
    TDateTime,
    TOptional,
    TRecord,
    TDynamicRec,
    TList,
    TIndexedList,
    TRow,
    THierarchy,
    TPath,
    TObject,
    TIface,
    )


def join_path( *args ):
    return '.'.join(filter(None, args))


class DecodeError(Exception): pass


class JsonDecoder(object):

    def __init__( self, peer, iface_registry, object_resolver=None ):
        self.peer = peer
        self.iface_registry = iface_registry  # IfaceRegistry
        self.object_resolver = object_resolver  # obj info -> handle

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
        base_fields = set()
        decoded_fields = {}
        while True:
            new_fields = [field for field in t.get_fields() if field.name not in base_fields]
            decoded_fields.update(self.decode_record_fields(new_fields, value, path, **kw))
            if t.want_peer_arg:
                decoded_fields.update(peer=self.peer)
            rec = t.instantiate_fixed(**decoded_fields)
            if not isinstance(t, TDynamicRec):
                return rec
            base_fields = set(field.name for field in t.get_fields())
            t = t.resolve_dynamic(rec)

    @dispatch.register(THierarchy)
    def decode_hierarchy_obj( self, t, value, path ):
        self.expect_type(path, isinstance(value, dict), value, 'hierarchy object (dict)')
        self.expect(path, '_class_id' in value, '_class_id field is missing')
        id = self.dispatch(TString(), value['_class_id'], join_path(path, '_class_id'))
        tclass = t.resolve(id)
        fields = self.decode_record_fields(tclass.get_fields(), value, path)
        return tclass.instantiate(**fields)

    def decode_record_fields( self, tfields, value, path, **kw ):
        fields = {}
        for field in tfields:
            self.expect(path, field.name in value, 'field %r is missing' % field.name)
            if field.type is not None:
                field_type = field.type
            else:  # open type
                field_type = kw[field.name]  # must be passed explicitly
            elt = self.dispatch(field_type, value[field.name], join_path(path, field.name))
            fields[field.name] = elt
        return fields

    @dispatch.register(TList)
    def decode_list( self, t, value, path ):
        self.expect_type(path, isinstance(value, list), value, 'list')
        return [self.dispatch(t.element_type, elt, join_path(path, '#%d' % idx))
                for idx, elt in enumerate(value)]

    @dispatch.register(TIndexedList)
    def decode_list( self, t, value, path ):
        self.expect_type(path, isinstance(value, list), value, 'list')
        decoded_elts = []
        for idx, elt in enumerate(value):
            decoded_elt = self.dispatch(t.element_type, elt, join_path(path, '#%d' % idx))
            setattr(decoded_elt, 'idx', idx)
            decoded_elts.append(decoded_elt)
        return decoded_elts

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
        assert self.object_resolver  # object decoding is not supported
        objinfo = self.decode_record(t, value, path)
        return self.object_resolver(objinfo)

    @dispatch.register(TIface)
    def decode_iface( self, t, value, path ):
        self.expect_type(path, isinstance(value, basestring), value, 'iface id (str)')
        iface_id = value
        return self.iface_registry.resolve(iface_id)
