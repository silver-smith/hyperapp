from . interface import (
    TString,
    TInt,
    Arg,
    Command,
    Interface,
    register_iface,
    )


file_iface = Interface('fs_file', [])
dir_iface = Interface('fs_dir', [
    Command('parent'),
    ])

register_iface(file_iface)
register_iface(dir_iface)
