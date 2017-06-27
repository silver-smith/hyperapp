from .htypes import (
    tString,
    Field,
    TRecord,
    TList,
    tPath,
    tIfaceId,
    )
from .hierarchy import THierarchy, TExceptionHierarchy
from .switched import tSwitched, TSwitchedRec
from .meta_type import TypeRegistry


def make_request_types():
    update = TSwitchedRec(['iface'], fields=[
        Field('iface', tIfaceId),
        Field('path', tPath),
        Field('diff', tSwitched),
        ])

    client_packet = THierarchy('client_packet')
    client_notification_rec = TSwitchedRec(['iface', 'command_id'], fields=[
        Field('iface', tIfaceId),
        Field('path', tPath),
        Field('command_id', tString),
        Field('params', tSwitched),
        ])
    client_notification = client_packet.register('notification', client_notification_rec)
    request = client_packet.register('request', TSwitchedRec(base=client_notification_rec, fields=[
        Field('request_id', tString),
        ]))

    error = TExceptionHierarchy('error')
    error_root = error.register('root')
    client_error = error.register('client_error', base=error_root)
    server_error = error.register('server_error', base=error_root)

    server_packet = THierarchy('server_packet')
    server_notification = server_packet.register('notification', fields=[
        Field('updates', TList(update)),
        ])
    response_rec = TRecord(base=server_notification, fields=[
                                Field('iface', tIfaceId),
                                Field('command_id', tString),
                                Field('request_id', tString),
                                ])
    result_response_rec = TSwitchedRec(['iface', 'command_id'],
                                base=response_rec, fields=[
                                Field('result', tSwitched),
                                ])
    error_response_rec = TRecord(base=response_rec, fields=[
                                Field('error', error),
                                ])
    response = server_packet.register('response')
    result_response = server_packet.register('result_response', result_response_rec, base=response)
    error_response = server_packet.register('error_response', error_response_rec, base=response)

    registry = TypeRegistry()
    registry.register('update', update)
    registry.register('client_packet', client_packet)
    registry.register('client_notification_rec', client_notification_rec)
    registry.register('client_notification', client_notification)
    registry.register('request', request)
    registry.register('error', error)
    registry.register('error_root', error_root)
    registry.register('client_error', client_error)
    registry.register('server_error', server_error)
    registry.register('server_packet', server_packet)
    registry.register('server_notification', server_notification)
    registry.register('response_rec', response_rec)
    registry.register('result_response_rec', result_response_rec)
    registry.register('error_response_rec', error_response_rec)
    registry.register('response', response)
    registry.register('result_response', result_response)
    registry.register('error_response', error_response)
    return registry
