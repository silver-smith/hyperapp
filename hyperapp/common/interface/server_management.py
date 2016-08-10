from ..htypes import (
    register_iface,
    Column,
    ElementOpenCommand,
    ListInterface,
    )


server_management_iface = ListInterface(
    'server_management',
    columns=[
        Column('key'),
        Column('module'),
        Column('text'),
        Column('desc'),
        ],
    commands=[
        ElementOpenCommand('open'),
        ])

register_iface(server_management_iface)
