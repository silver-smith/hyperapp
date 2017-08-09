from .method_dispatch import method_dispatch
from .htypes import (
    TPrimitive,
    TOptional,
    TRecord,
    TEmbedded,
    THierarchy,
    TList,
    )


class Visitor(object):

    def __init__(self, packet_types, core_types, iface_registry):
        self._packet_types = packet_types
        self._core_types = core_types
        self._iface_registry = iface_registry

    def visit(self, t, value):
        self.dispatch(t, value)

    def visit_record(self, t, value):
        pass

    def visit_hierarchy_obj(self, t, tclass, value):
        pass

    @method_dispatch
    def dispatch(self, t, value):
        assert False, repr((t, value))  # Unknown type

    @dispatch.register(TPrimitive)
    def process_primitive(self, t, value):
        pass

    @dispatch.register(TOptional)
    def process_optional(self, t, value):
        if value is not None:
            self.dispatch(t.base_t, value)

    @dispatch.register(TRecord)
    def process_record(self, t, value):
        self.visit_record(t, value)
        fields = {}
        for field in t.get_static_fields():
            field_val = getattr(value, field.name)
            self.dispatch(field.type, field_val)
            fields[field.name] = field_val
            
    @dispatch.register(TEmbedded)
    def process_embedded(self, t, value):
        pass
            
    @dispatch.register(THierarchy)
    def process_hierarchy_obj(self, t, value):
        tclass = t.resolve_obj(value)
        self.visit_hierarchy_obj(t, tclass, value)
        self.dispatch(tclass.get_trecord(), value)
        if issubclass(tclass, self._packet_types.client_packet):
            self.visit_client_packet_params(value)
        if issubclass(tclass, self._packet_types.server_result_response):
            self.visit_server_response_result(value)
        if issubclass(tclass, self._packet_types.server_error_response):
            self.visit_server_response_error(value)

    def process_field(self, field, value):
        self.dispatch(field.type, getattr(value, field.name))

    @dispatch.register(TList)
    def process_list(self, t, value):
        for elt in value:
            self.dispatch(t.element_t, elt)

    def visit_client_packet_params(self, client_packet):
        iface = self._iface_registry.resolve(client_packet.iface)
        params_t = iface.get_command(client_packet.command_id).params_type
        params = client_packet.params.decode(params_t)
        self.visit(params_t, params)

    def visit_server_response_result(self, server_result_response):
        iface = self._iface_registry.resolve(server_result_response.iface)
        result_t = iface.get_command(server_result_response.command_id).result_type
        result = server_result_response.result.decode(result_t)
        self.visit(result_t, result)

    def visit_server_response_error(self, server_error_response):
        error = server_error_response.error.decode(self._packet_types.error)
        self.visit(self._packet_types.error, error)
