import logging
import json
from .method_dispatch import method_dispatch
from .util import encode_path, encode_route
from .htypes import (
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
    tUrl,
    tTypeModule,
    )
from .identity import PublicKey

log = logging.getLogger(__name__)


class RepNode(object):

    def __init__(self, text, children=None):
        self.text = text
        self.children = children or []

    def pprint(self, indent=0):
        log.info('%s%s' % ('  ' * indent, self.text))
        for node in self.children:
            node.pprint(indent + 1)


class VisualRepEncoder(object):

    def __init__(self, resource_types=None, packet_types=None):
        self._resource_types = resource_types
        self._packet_types = packet_types

    def encode(self, t, value):
        return self.dispatch(t, value)

    @method_dispatch
    def dispatch(self, t, value):
        assert False, repr((t, value))  # Unknown type

    @dispatch.register(TString)
    @dispatch.register(TInt)
    @dispatch.register(TBool)
    def encode_primitive(self, t, value):
        return RepNode(repr(value))

    @dispatch.register(TBinary)
    def encode_binary(self, t, value):
        return RepNode('binary, len=%d' % len(value))

    @dispatch.register(TDateTime)
    def encode_datetime(self, t, value):
        return RepNode(value.isoformat())

    @dispatch.register(TOptional)
    def encode_optional(self, t, value):
        if value is None:
            return RepNode('None')
        return self.dispatch(t.base_t, value)

    @dispatch.register(TRecord)
    def encode_record(self, t, value):
        ## print '*** encoding record', value, t, [field.name for field in t.get_fields()]
        if self._packet_types and t is self._packet_types.module:
            return RepNode('module: id=%s, package=%s, satisfies=%r' % (value.id, value.package, value.satisfies))
        if t is tCommand:
            return RepNode('command: command_id=%r, kind=%r, resource_id=%s, is_default_command=%s'
                           % (value.command_id, value.kind, encode_path(value.resource_id), value.is_default_command))
        if t is tTypeModule:
            return self._make_type_module_rep(value)
        children = self.encode_record_fields(t, value)
        if t is tServerRoutes:
            public_key = PublicKey.from_der(value.public_key_der)
            return RepNode('server routes: %s -> %r'
                           % (public_key.get_short_id_hex(), [encode_route(route) for route in value.routes]))
        if t is tUrl:
            public_key = PublicKey.from_der(value.public_key_der)
            return RepNode('iface=%s public_key=%s, path=%s'
                           % (value.iface, public_key.get_short_id_hex(), encode_path(value.path)))
        if children:
            return RepNode('record', children)
        else:
            return RepNode('empty record')

    def _make_type_module_rep(self, type_module):
        return RepNode('type module %r' % type_module.module_name, children=[
            RepNode('provided: %s' % ', '.join('%s/%s' % (pc.hierarchy_id, pc.class_id) for pc in type_module.provided_classes)),
            RepNode('used_modules: %s' % ', '.join(type_module.used_modules)),
            RepNode('%d typedefs: %s' % (len(type_module.typedefs), ', '.join(typedef.name for typedef in type_module.typedefs))),
            ])

    def encode_record_fields(self, t, value):
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
    def encode_hierarchy_obj(self, t, value):
        tclass = t.resolve_obj(value)
        children = self.encode_record_fields(tclass.get_trecord(), value)
        return RepNode('%s %r' % (t.hierarchy_id, tclass.id), children)

    def field_rep(self, field, value):
        rep = self.dispatch(field.type, getattr(value, field.name))
        return RepNode('%s=%s' % (field.name, rep.text), rep.children)

    @dispatch.register(TList)
    def encode_list(self, t, value):
        if t is tPath:
            return self.encode_path(value)
        if self._packet_types and t is self._packet_types.requirement:
            return RepNode('requirement: %s' % '/'.join(value))
        if self._packet_types and t is self._resource_types.resource_id:
            return RepNode(encode_path(value))
        children = [self.dispatch(t.element_t, elt) for elt in value]
        return RepNode('list (with %d elements)' % len(value), children)

    def encode_path(self, obj):
        return RepNode(encode_path(obj))


def pprint(t, value, resource_types=None, packet_types=None):
    rep = VisualRepEncoder(resource_types, packet_types).encode(t, value)
    rep.pprint()
