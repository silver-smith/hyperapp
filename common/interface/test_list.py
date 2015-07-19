from . types import (
    tString,
    )
from . interface import register_iface
from . list import ListInterface


test_list_iface = ListInterface('test_list', columns=[tString, tString, tString, tString], commands=[
    ])

register_iface(test_list_iface)
