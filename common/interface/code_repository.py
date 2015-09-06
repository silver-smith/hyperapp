from . interface import OpenCommand, register_iface
from . list import stringColumnType, Column, ListInterface


module_list_iface = ListInterface(
    'module_list',
    columns=[
        Column('name', 'Default name', stringColumnType),
        Column('id', 'Module id', stringColumnType),
        ],
    commands=[
    ],
    key_column='id')

register_iface(module_list_iface)
