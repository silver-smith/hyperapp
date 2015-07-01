from . types import TString
from . interface import register_iface
from . list import ElementOpenCommand, ListInterface


server_management_iface = ListInterface('server_management',
                                        columns=[TString(), TString(), TString()],
                                        commands=[
                                            ElementOpenCommand('open'),
                                            ])

register_iface(server_management_iface)
