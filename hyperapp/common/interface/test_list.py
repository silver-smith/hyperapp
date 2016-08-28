from ..htypes import (
    tString,
    tInt,
    Field,
    register_iface,
    RequestCmd,
    OpenCommand,
    Interface,
    Column,
    ListInterface,
    )
from .form import tStringFieldHandle, tIntFieldHandle, tFormHandle


params_form_iface = Interface('test_list_params', commands=[
    OpenCommand('submit', [Field('key', tInt), Field('size', tInt)]),
    ])

test_list_iface = ListInterface('test_list', columns=[
        Column('key', tInt, is_key=True),
        Column('field_1'),
        Column('field_2'),
        Column('field_3'),
    ], commands=[
        OpenCommand('params'),
    ])

register_iface(params_form_iface)
register_iface(test_list_iface)
