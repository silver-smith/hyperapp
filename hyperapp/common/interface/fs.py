from ..htypes import (
    tString,
    tInt,
    Field,
    OpenCommand,
    Interface,
    register_iface,
    intColumnType,
    Column,
    ElementCommand,
    ElementOpenCommand,
    ListInterface,
    )


file_iface = ListInterface('fs_file', columns=[
    Column('idx', intColumnType),
    Column('line'),
    ], key_column='idx')

dir_iface = ListInterface('fs_dir', columns=[
        Column('key'),
        Column('ftype'),
        Column('ftime', intColumnType),
        Column('fsize', intColumnType),
    ], commands=[
        OpenCommand('parent'),
        ElementOpenCommand('open'),
    ])

register_iface(file_iface)
register_iface(dir_iface)
