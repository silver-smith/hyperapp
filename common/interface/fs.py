from . interface import (
    TString,
    TInt,
    Field,
    Command,
    ElementCommand,
    Interface,
    ListInterface,
    register_iface,
    )


file_iface = ListInterface('fs_file', [TInt(), TString()], key_type=TInt())
dir_iface = ListInterface('fs_dir', [TString(), TString(), TInt(), TInt()], [
    Command('parent'),
    ElementCommand('open'),
    ])

register_iface(file_iface)
register_iface(dir_iface)
