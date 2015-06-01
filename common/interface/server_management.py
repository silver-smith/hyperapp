from . interface import (
    TString,
    TInt,
    Field,
    Command,
    ElementCommand,
    ListInterface,
    register_iface,
    )


server_management_iface = ListInterface('server_management',
                                        columns=[TString(), TString(), TString()],
                                        commands=[
                                            ElementCommand('open'),
                                            ])

register_iface(server_management_iface)
