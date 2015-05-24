from . interface import (
    TString,
    TInt,
    Field,
    Command,
    ElementCommand,
    Interface,
    register_iface,
    )


server_management_iface = Interface('server_management', [
    ElementCommand('open'),
    ])

register_iface(server_management_iface)
