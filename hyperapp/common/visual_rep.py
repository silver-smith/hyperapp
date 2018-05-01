import logging
import json
import codecs

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
    TEmbedded,
    THierarchy,
    TClass,
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

    def __init__(self, resource_types=None, error_types=None, packet_types=None, iface_registry=None, module_types=None):
        self._resource_types = resource_types
        self._error_types = error_types
        self._packet_types = packet_types
        self._iface_registry = iface_registry
        self._module_types = module_types

    def encode(self, t, value):
        assert isinstance(value, t), repr(value)
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
        return RepNode('binary, len=%d: %s' % (len(value), codecs.encode(value[:40], 'hex')))

    @dispatch.register(TDateTime)
    def encode_datetime(self, t, value):
        return RepNode(value.isoformat())

    @dispatch.register(TOptional)
    def encode_optional(self, t, value):
        if value is None:
            return RepNode('None')
        return self.dispatch(t.base_t, value)

    @staticmethod
    def _make_name(t, type_name):
        if t.full_name:
            return '%s (%s)' % ('.'.join(t.full_name), type_name)
        else:
            return type_name

    @dispatch.register(TList)
    def encode_list(self, t, value):
        if t is tPath:
            return self.encode_path(value)
        if self._module_types and t is self._module_types.requirement:
            return RepNode('requirement: %s' % ':'.join(value))
        if self._resource_types and t is self._resource_types.resource_id:
            return RepNode(encode_path(value))
        children = [self.dispatch(t.element_t, elt) for elt in value]
        return RepNode('%s (%d elements)' % (self._make_name(t, 'list'), len(value)), children)

    @dispatch.register(TRecord)
    def encode_record(self, t, value):
        ## print '*** encoding record', value, t, [field.name for field in t.fields]
        if self._module_types and t is self._module_types.module:
            return RepNode('module: id=%s, package=%s, satisfies=%r' % (value.id, value.package, value.satisfies))
        if t is tCommand:
            return RepNode('command: command_id=%r, kind=%r, resource_id=%s'
                           % (value.command_id, value.kind, encode_path(value.resource_id)))
        if t is tTypeModule:
            return self._make_type_module_rep(value)
        custom_encoders = None
        if self._packet_types and self._iface_registry and issubclass(t, self._packet_types.update):
            custom_encoders = dict(diff=self.encode_update_diff)
        children = self.encode_record_fields(t.fields, value, custom_encoders)
        if t is tServerRoutes:
            public_key = PublicKey.from_der(value.public_key_der)
            return RepNode('server routes: %s -> %r'
                           % (public_key.get_short_id_hex(), [encode_route(route) for route in value.routes]))
        if t is tUrl:
            public_key = PublicKey.from_der(value.public_key_der)
            return RepNode('iface=%s public_key=%s, path=%s'
                           % (value.iface, public_key.get_short_id_hex(), encode_path(value.path)))
        if children:
            return RepNode(self._make_name(t, 'record'), children)
        else:
            return RepNode('%s: empty' % self._make_name(t, 'record'))

    def _make_type_module_rep(self, type_module):
        return RepNode('type module %r' % type_module.module_name, children=[
            RepNode('provided classes: %s' % ', '.join('%s/%s' % (pc.hierarchy_id, pc.class_id) for pc in type_module.provided_classes)),
            RepNode('used_modules: %s' % ', '.join(type_module.used_modules)),
            RepNode('%d typedefs: %s' % (len(type_module.typedefs), ', '.join(typedef.name for typedef in type_module.typedefs))),
            ])

    def encode_record_fields(self, fields, value, custom_encoders=None):
        children = []
        for field in fields:
            custom_encoder = (custom_encoders or {}).get(field.name)
            rep = self.field_rep(field, value, custom_encoder)
            children.append(rep)
        return children

    def field_rep(self, field, value, custom_encoder):
        if custom_encoder:
            rep = custom_encoder(value)
        else:
            rep = self.dispatch(field.type, getattr(value, field.name))
        return RepNode('%s=%s' % (field.name, rep.text), rep.children)

    @dispatch.register(TEmbedded)
    def encode_list(self, t, value):
        return RepNode('<%s>' % self._make_name(t, 'embedded'))

    @dispatch.register(THierarchy)
    def encode_hierarchy_obj(self, t, value):
        tclass = t.get_object_class(value)
        custom_encoders = {}
        if self._packet_types and self._iface_registry:
            if issubclass(tclass, self._packet_types.client_packet):
                custom_encoders = dict(params=self.encode_client_packet_params)
            if issubclass(tclass, self._packet_types.server_result_response):
                custom_encoders = dict(result=self.encode_server_response_result)
            if issubclass(tclass, self._packet_types.server_error_response):
                custom_encoders = dict(error=self.encode_error_response_error)
        children = self.encode_record_fields(tclass.get_fields(), value, custom_encoders)
        return RepNode('%s %r %r' % (self._make_name(t, 'hierarchy'), t.hierarchy_id, tclass.id), children)

    @dispatch.register(TClass)
    def encode_tclass_obj(self, t, value):
        assert isinstance(value, t), repr((t, value))
        return self.encode_hierarchy_obj(t.hierarchy, value)

    def encode_path(self, obj):
        return RepNode(encode_path(obj))

    def encode_client_packet_params(self, client_packet):
        iface = self._iface_registry.resolve(client_packet.iface)
        params_t = iface.get_command(client_packet.command_id).params_type
        params = client_packet.params.decode(params_t)
        return self.dispatch(params_t, params)

    def encode_server_response_result(self, server_result_response):
        iface = self._iface_registry.resolve(server_result_response.iface)
        result_t = iface.get_command(server_result_response.command_id).result_type
        result = server_result_response.result.decode(result_t)
        return self.dispatch(result_t, result)

    def encode_error_response_error(self, server_error_response):
        error = server_error_response.error.decode(self._error_types.error)
        return self.dispatch(self._error_types.error, error)

    def encode_update_diff(self, update):
        iface = self._iface_registry.resolve(update.iface)
        diff = update.diff.decode(iface.diff_type)
        return self.dispatch(iface.diff_type, diff)

def pprint(t, value, resource_types=None, error_types=None, packet_types=None, iface_registry=None, module_types=None):
    rep = VisualRepEncoder(resource_types, error_types, packet_types, iface_registry, module_types).encode(t, value)
    rep.pprint()
