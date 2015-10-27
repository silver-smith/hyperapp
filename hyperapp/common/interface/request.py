from .iface_types import (
    tString,
    Field,
    TRecord,
    TList,
    tUrl,
    tIfaceId,
    )
from .hierarchy import THierarchy
from .switched import tSwitched, TSwitchedRec


tUpdate = TSwitchedRec(['iface'], fields=[
    Field('iface', tIfaceId),
    Field('path', tUrl),
    Field('diff', tSwitched),
    ])


tClientPacket = THierarchy('client_packet')

tClientNotificationRec = TSwitchedRec(['iface', 'command_id'], fields=[
    Field('iface', tIfaceId),
    Field('path', tUrl),
    Field('command_id', tString),
    Field('params', tSwitched),
    ])

tClientNotification = tClientPacket.register('notification', tClientNotificationRec)

tRequest = tClientPacket.register('request', TSwitchedRec(base=tClientNotificationRec, fields=[
    Field('request_id', tString),
    ]))


tServerPacket = THierarchy('server_packet')

tServerNotification = tServerPacket.register('notification', fields=[
    Field('updates', TList(tUpdate)),
    ])

tResponseRec = TSwitchedRec(['iface', 'command_id'],
                            base=tServerNotification, fields=[
                                Field('iface', tIfaceId),
                                Field('command_id', tString),
                                Field('request_id', tString),
                                Field('result', tSwitched),
                                ])
tResponse = tServerPacket.register('response', tResponseRec)
