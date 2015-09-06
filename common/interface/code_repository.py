from . types import (
    tString,
    Field,
    )
from . interface import OpenCommand, Interface, register_iface
from . list import stringColumnType, Column, ElementOpenCommand, ListInterface


module_list_iface = ListInterface(
    'module_list',
    columns=[
        Column('name', 'Default name', stringColumnType),
        Column('id', 'Module id', stringColumnType),
        ],
    commands=[
        ElementOpenCommand('open'),
    ],
    key_column='id')


module_form_iface = Interface('module_form', commands=[
    OpenCommand('submit', [Field('name', tString)]),
    ])


register_iface(module_list_iface)
register_iface(module_form_iface)
