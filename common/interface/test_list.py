from . types import (
    tString,
    tInt,
    Field,
    )
from . interface import register_iface, OpenCommand, Interface
from . list import ListInterface
from . form import tStringFieldHandle, tIntFieldHandle, tFormHandle


params_form_iface = Interface('test_list_params', commands=[
    ])

test_list_iface = ListInterface('test_list', key_type=tInt, columns=[tString, tString, tString, tString], commands=[
    OpenCommand('params'),
    ])

register_iface(params_form_iface)
register_iface(test_list_iface)
