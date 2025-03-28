from . import htypes
from .tested.code import command_args


def test_args_t_dict_to_tuple():
    args = {
        'name': htypes.builtin.int,
        }
    result = command_args.args_t_dict_to_tuple(args)
    assert type(result) is tuple


def test_args_dict_to_tuple():
    args = {
        'name': 123,
        }
    result = command_args.args_dict_to_tuple(args)
    assert type(result) is tuple
