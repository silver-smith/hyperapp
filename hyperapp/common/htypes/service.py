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


def register_service_types(builtin_types, mosaic, types):
    builtin_types.register(mosaic, types, service_t)
