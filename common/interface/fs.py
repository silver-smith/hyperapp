from . interface import (
    TString,
    TInt,
    Field,
    Command,
    OpenCommand,
    ElementCommand,
    ElementOpenCommand,
    Interface,
    ListInterface,
    register_iface,
    )


file_iface = ListInterface('fs_file', columns=[TInt(), TString()], key_type=TInt())
dir_iface = ListInterface('fs_dir', columns=[TString(), TString(), TInt(), TInt()], commands=[
    OpenCommand('parent'),
    ElementOpenCommand('open'),
    ])

register_iface(file_iface)
register_iface(dir_iface)
