from ..htypes import (
    tString,
    tBinary,
    Field,
    register_iface,
    Column,
    ListInterface,
    OpenCommand,
    )


user_list_iface = ListInterface(
    'user_list',
    key_column='id',
    columns=[
        Column('id'),
        Column('user_name', 'User name'),
        Column('public_key_id', 'Public key id'),
        ],
    commands=[
        OpenCommand('add', [Field('user_name', tString),
                            Field('public_key_der', tBinary)]),
        ])

register_iface(user_list_iface)
