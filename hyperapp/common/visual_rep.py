import logging
import json
from .method_dispatch import method_dispatch
from .util import encode_path, encode_route
from .htypes import (
    TPrimitive,
    TString,
    TBinary,
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
    tPath,
    tCommand,
    tServerRoutes,
    )
from .identity import PublicKey
from .interface.code_repository import tModule, tRequirement

log = logging.getLogger(__name__)


class RepNode(object):

    def __init__( self, text, children=None ):
        self.text = text
        self.children = children or []

    def pprint( self, indent=0 ):
        log.info('%s%s' % ('  ' * indent, self.text))
        for node in self.children:
            node.pprint(indent + 1)


class VisualRepEncoder(object):

    def encode( self, t, value ):
        return self.dispatch(t, value)

    @method_dispatch
    def dispatch( self, t, value ):
        assert False, repr((t, value))  # Unknown type

    @dispatch.register(TString)
    @dispatch.register(TInt)
    @dispatch.register(TBool)
    def encode_primitive( self, t, value ):
        return RepNode(repr(value))

    @dispatch.register(TBinary)
    def encode_binary( self, t, value ):
        return RepNode('binary, len=%d' % len(value))

    @dispatch.register(TDateTime)
    def encode_datetime( self, t, value ):
        return RepNode(value.isoformat())

    @dispatch.register(TOptional)
    def encode_optional( self, t, value ):
        if value is None:
            return RepNode('None')
        return self.dispatch(t.type, value)

    @dispatch.register(TRecord)
    def encode_record( self, t, value ):
        ## print '*** encoding record', value, t, [field.name for field in t.get_fields()]
        if t is tModule:
            return RepNode('module: id=%s, package=%s, satisfies=%r' % (value.id, value.package, value.satisfies))
        children = self.encode_record_fields(t, value)
        if t is tCommand:
            return RepNode('command: %s' % ', '.join(child.text for child in children))
        if t is tServerRoutes:
            public_key = PublicKey.from_der(value.public_key_der)
            return RepNode('server routes: %s -> %r'
                           % (public_key.get_short_id_hex(), [encode_route(route) for route in value.routes]))
        ## if t is tEndpoint:
        ##     endpoint = Endpoint.from_data(value)
        ##     return RepNode('endpoint: %s -> %r'
        ##                    % (endpoint.public_key.get_short_id_hex(), [encode_route(route) for route in endpoint.routes]))
        if children:
            return RepNode('record', children)
        else:
            return RepNode('empty record')

    def encode_record_fields( self, t, value ):
        children = []
        fields = {}
        for field in t.get_static_fields():
            children.append(self.field_rep(field, value))
            fields[field.name] = getattr(value, field.name)
        if isinstance(t, TSwitchedRec):
            field = t.get_dynamic_field(fields)
            children.append(self.field_rep(field, value))
        return children

    @dispatch.register(THierarchy)
    def encode_hierarchy_obj( self, t, value ):
        tclass = t.resolve_obj(value)
        children = self.encode_record_fields(tclass.get_trecord(), value)
        return RepNode('%s %r' % (t.hierarchy_id, tclass.id), children)

    def field_rep( self, field, value ):
        rep = self.dispatch(field.type, getattr(value, field.name))
        return RepNode('%s=%s' % (field.name, rep.text), rep.children)

    @dispatch.register(TList)
    def encode_list( self, t, value ):
        if t is tPath:
            return self.encode_path(value)
        if t is tRequirement:
            return RepNode('requirement: %s' % '/'.join(value))
        children = [self.dispatch(t.element_type, elt) for elt in value]
        return RepNode('list (with %d elements)' % len(value), children)

    def encode_path( self, obj ):
        return RepNode(encode_path(obj))


def pprint( t, value ):
    rep = VisualRepEncoder().encode(t, value)
    rep.pprint()
