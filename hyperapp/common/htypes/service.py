from .htypes import Type, TList, tString
from .record import TRecord, ref_t
from .interface import Interface, Request


service_command_t = TRecord('service_command', {
    'id': tString,
    'command_ref': ref_t,
    })

service_t = TRecord('service', {
    'type_ref': ref_t,  # service type
    'peer_ref': ref_t,
    'object_id': tString,
    'command_list': TList(service_command_t),
    })

list_service_t = TRecord('list_service', base=service_t)

record_field_t = TRecord('record_field', {
    'id': tString,
    'type_ref': ref_t,
    })

record_service_t = TRecord('record_service', base=service_t, fields={
    'field_list': TList(record_field_t),
    })


def register_service_types(builtin_types, mosaic, types):
    builtin_types.register(mosaic, types, service_t)
    builtin_types.register(mosaic, types, list_service_t)
    builtin_types.register(mosaic, types, record_service_t)
