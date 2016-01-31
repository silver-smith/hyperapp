from ..htypes import (
    tString,
    tInt,
    Field,
    register_iface,
    RequestCmd,
    OpenCommand,
    Interface,
    intColumnType,
    Column,
    ListInterface,
    )
from .form import tStringFieldHandle, tIntFieldHandle, tFormHandle


params_form_iface = Interface('test_list_params', commands=[
    OpenCommand('submit', [Field('key', tInt), Field('size', tInt)]),
    ])

test_list_iface = ListInterface('test_list', columns=[
        Column('key', type=intColumnType),
        Column('field_1', 'Field #1'),
        Column('field_2', 'Field #2'),
        Column('field_3', 'Field #3'),
    ], commands=[
        OpenCommand('params'),
    ],
    required_module_id=globals().get('this_module_id'))

register_iface(params_form_iface)
register_iface(test_list_iface)
