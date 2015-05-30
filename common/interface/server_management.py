from . interface import (
    TString,
    TInt,
    Field,
    Command,
    ElementCommand,
    ListInterface,
    register_iface,
    )


server_management_iface = ListInterface('server_management', [], [
    ElementCommand('open'),
    ])

register_iface(server_management_iface)
