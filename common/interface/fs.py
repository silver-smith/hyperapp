from . types import (
    tString,
    tInt,
    Field,
    )
from . interface import OpenCommand, Interface, register_iface
from . list import ElementCommand, ElementOpenCommand, ListInterface


file_iface = ListInterface('fs_file', columns=[tInt, tString], key_type=tInt)
dir_iface = ListInterface('fs_dir', columns=[tString, tString, tInt, tInt], commands=[
    OpenCommand('parent'),
    ElementOpenCommand('open'),
    ])

register_iface(file_iface)
register_iface(dir_iface)
