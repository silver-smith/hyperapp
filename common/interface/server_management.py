from . interface import (
    TString,
    TInt,
    Field,
    Command,
    Interface,
    register_iface,
    )


server_management_iface = Interface('server_management', [])

register_iface(server_management_iface)
