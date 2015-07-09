from . types import tString
from . interface import register_iface
from . list import ElementOpenCommand, ListInterface


server_management_iface = ListInterface('server_management',
                                        columns=[tString, tString, tString],
                                        commands=[
                                            ElementOpenCommand('open'),
                                            ])

register_iface(server_management_iface)
