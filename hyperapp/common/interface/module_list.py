from ..htypes import (
    tString,
    Field,
    OpenCommand,
    Interface,
    register_iface,
    Column,
    ElementCommand,
    ElementOpenCommand,
    ListInterface,
    )


module_list_iface = ListInterface(
    'module_list',
    columns=[
        Column('name'),
        Column('id', is_key=True),
        ],
    commands=[
        OpenCommand('add'),
        ElementCommand('delete'),
        ElementOpenCommand('open'),
        ElementOpenCommand('deps'),
    ])

module_form_iface = Interface('module_form', commands=[
    OpenCommand('submit', [Field('name', tString)]),
    ])


module_dep_list_iface = ListInterface(
    'module_deps_list',
    columns=[
        Column('dep_id', is_key=True),
        Column('visible_as'),
        Column('id'),
        ],
    commands=[
        ElementCommand('remove'),
    ])

available_dep_list_iface = ListInterface(
    'available_deps_list',
    columns=[
        Column('name'),
        Column('id', is_key=True),
        ],
    commands=[
        ElementCommand('add'),
    ])



register_iface(module_list_iface)
register_iface(module_form_iface)
register_iface(module_dep_list_iface)
register_iface(available_dep_list_iface)
