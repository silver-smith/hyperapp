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
    Column('idx', 'Index', intColumnType),
    Column('line', 'Line'),
    ], key_column='idx')

dir_iface = ListInterface('fs_dir', columns=[
        Column('key', 'File Name'),
        Column('ftype', 'File type'),
        Column('ftime', 'Modification time', intColumnType),
        Column('fsize', 'File size', intColumnType),
    ], commands=[
        OpenCommand('parent'),
        ElementOpenCommand('open'),
    ])

register_iface(file_iface)
register_iface(dir_iface)
