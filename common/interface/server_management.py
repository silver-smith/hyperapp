from . interface import (
    TString,
    TInt,
    Field,
    Command,
    ElementCommand,
    ElementOpenCommand,
    ListInterface,
    register_iface,
    )


server_management_iface = ListInterface('server_management',
                                        columns=[TString(), TString(), TString()],
                                        commands=[
                                            ElementOpenCommand('open'),
                                            ])

register_iface(server_management_iface)
