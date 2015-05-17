from . interface import (
    TString,
    TInt,
    Arg,
    Command,
    Interface,
    register_iface,
    )


server_management_iface = Interface('server_management', [])

register_iface(server_management_iface)
