import json
from .method_dispatch import method_dispatch
from .util import encode_url
from .interface import (
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
    THierarchy,
    Interface,
    tUrl,
    tCommand,
    tModule,
    tRequirement,
    )


class RepNode(object):

    def __init__( self, text, children=None ):
        self.text = text
        self.children = children or []

    def pprint( self, indent=0 ):
        print '%s%s' % ('  ' * indent, self.text)
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
        children = []
        base_fields = set()
        while True:
            new_fields = [field for field in t.get_fields() if field.name not in base_fields]
            for field in new_fields:
                children.append(self.field_rep(field, value))
            if not isinstance(t, TDynamicRec):
                break
            base_fields = set(field.name for field in t.get_fields())
            t = t.resolve_dynamic(value)
        if t is tModule:
            return RepNode('module: id=%s, package=%s, satisfies=%r' % (value.id, value.package, value.satisfies))
        if t is tCommand:
            return RepNode('command: %s' % ', '.join(child.text for child in children))
        return RepNode('record', children)

    @dispatch.register(THierarchy)
    def encode_hierarchy_obj( self, t, value ):
        tclass = t.resolve_obj(value)
        children = []
        for field in tclass.get_fields():
            children.append(self.field_rep(field, value))
        return RepNode('class %r' % tclass.id, children)

    def field_rep( self, field, value ):
        rep = self.dispatch(field.type, getattr(value, field.name))
        return RepNode('%s=%s' % (field.name, rep.text), rep.children)

    @dispatch.register(TList)
    def encode_list( self, t, value ):
        if t is tUrl:
            return self.encode_url(value)
        if t is tRequirement:
            return RepNode('requirement: %s' % '/'.join(value))
        children = [self.dispatch(t.element_type, elt) for elt in value]
        return RepNode('list (with %d elements)' % len(value), children)

    def encode_url( self, obj ):
        return RepNode(encode_url(obj))


def pprint( t, value ):
    rep = VisualRepEncoder().encode(t, value)
    rep.pprint()
