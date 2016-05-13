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
        Column('module', 'Module'),
        Column('text', 'Name'),
        ],
    commands=[
        ElementOpenCommand('open'),
        ])

register_iface(server_management_iface)
