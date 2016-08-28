from ..htypes import (
    tString,
    tInt,
    Field,
    OpenCommand,
    Interface,
    register_iface,
    Column,
    ElementCommand,
    ElementOpenCommand,
    ListInterface,
    )


file_iface = ListInterface('fs_file', columns=[
    Column('idx', tInt, is_key=True),
    Column('line'),
    ])

dir_iface = ListInterface('fs_dir', columns=[
        Column('key', is_key=True),
        Column('ftype'),
        Column('ftime', tInt),
        Column('fsize', tInt),
    ], commands=[
        OpenCommand('parent'),
        ElementOpenCommand('open'),
    ])

register_iface(file_iface)
register_iface(dir_iface)
