from .iface_types import (
    tString,
    Field,
    TRecord,
    TList,
    tUrl,
    tIfaceId,
    )
from .hierarchy import THierarchy


tParams = THierarchy('params')
tResult = THierarchy('result')


tUpdate = THierarchy('update')
tUpdateBase = tUpdate.register('base', fields=[
    Field('iface', tIfaceId),
    Field('path', tUrl),
    ])

def register_diff( id, diff_type ):
    tUpdate.register(id, base=tUpdateBase, fields=[Field('diff', diff_type)])


tServerPacket = THierarchy('server_packet')

tServerNotification = tServerPacket.register('notification', fields=[
    Field('updates', TList(tUpdate)),
    ])

tResponseBase = tServerPacket.register('response', base=tServerNotification, fields=[
    Field('iface', tIfaceId),
    Field('command_id', tString),
    Field('request_id', tString),
    Field('result', tResult),
    ])

def register_response_type( id, type ):
    return tServerPacket.register(id, base=tResponseBase, fields=[Field('result', type)])


tClientPacket = THierarchy('client_packet')

tClientNotification = tClientPacket.register('notification', fields=[
    Field('iface', tIfaceId),
    Field('path', tUrl),
    Field('command_id', tString),
    Field('params', tParams),
    ])

tRequest = tClientPacket.register('request', base=tClientNotification, fields=[
    Field('request_id', tString),
    ])
