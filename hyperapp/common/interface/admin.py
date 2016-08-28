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
    columns=[
        Column('id', is_key=True),
        Column('user_name'),
        Column('public_key_id'),
        ],
    commands=[
        OpenCommand('add', [Field('user_name', tString),
                            Field('public_key_der', tBinary)]),
        ])

register_iface(user_list_iface)
