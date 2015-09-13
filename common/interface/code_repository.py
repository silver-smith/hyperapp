from . types import (
    tString,
    Field,
    )
from . interface import OpenCommand, Interface, register_iface
from . list import stringColumnType, intColumnType, Column, ElementCommand, ElementOpenCommand, ListInterface


module_list_iface = ListInterface(
    'module_list',
    columns=[
        Column('name', 'Default name', stringColumnType),
        Column('id', 'Module id', stringColumnType),
        ],
    commands=[
        OpenCommand('add'),
        ElementCommand('delete'),
        ElementOpenCommand('open'),
        ElementOpenCommand('deps'),
    ],
    key_column='id')

module_form_iface = Interface('module_form', commands=[
    OpenCommand('submit', [Field('name', tString)]),
    ])


module_dep_list_iface = ListInterface(
    'module_deps_list',
    columns=[
        Column('dep_id', type=intColumnType),
        Column('visible_as', 'Visible as', stringColumnType),
        Column('id', 'Module id', stringColumnType),
        ],
    commands=[
        ElementCommand('remove'),
    ],
    key_column='dep_id')

available_dep_list_iface = ListInterface(
    'available_deps_list',
    columns=[
        Column('name', 'Default name', stringColumnType),
        Column('id', 'Module id', stringColumnType),
        ],
    commands=[
        ElementCommand('add'),
    ],
    key_column='id')



register_iface(module_list_iface)
register_iface(module_form_iface)
register_iface(module_dep_list_iface)
register_iface(available_dep_list_iface)
