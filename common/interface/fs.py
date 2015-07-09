from . types import (
    tString,
    TInt,
    Field,
    )
from . interface import OpenCommand, Interface, register_iface
from . list import ElementCommand, ElementOpenCommand, ListInterface


file_iface = ListInterface('fs_file', columns=[TInt(), tString], key_type=TInt())
dir_iface = ListInterface('fs_dir', columns=[tString, tString, TInt(), TInt()], commands=[
    OpenCommand('parent'),
    ElementOpenCommand('open'),
    ])

register_iface(file_iface)
register_iface(dir_iface)
