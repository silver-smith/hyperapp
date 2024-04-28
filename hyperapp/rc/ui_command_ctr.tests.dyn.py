from . import htypes
from .services import (
    local_types,
    mosaic,
    pyobj_creg,
    )
from .tested.code import ui_command_ctr


def make_module_res():
    return htypes.builtin.python_module(
        module_name='ui_command_ctr_tests',
        source='',
        file_path='/ui_command_ctr_tests.dyn.py',
        import_list=(),
        )


def make_inspect_attr():
    return htypes.inspect.attr(
        name='sample_command',
        module=None,
        constructors=(),
        )


def _test_construct_ui_command(command_ctr_t, fn):
    module_res = make_module_res()
    string_res = pyobj_creg.reverse_resolve(htypes.builtin.string)
    name_to_res = {}
    fn(
        piece=command_ctr_t(
            t=mosaic.put(string_res),
            name='sample_command',
            params=('piece', 'state'),
            ),
        custom_types=local_types,
        name_to_res=name_to_res,
        module_res=module_res,
        attr=make_inspect_attr(),
        )
    assert 'sample_command.ui_command' in name_to_res


def test_construct_ui_command():
    _test_construct_ui_command(
        htypes.rc_constructors.ui_command_ctr, ui_command_ctr.construct_ui_command)


def test_construct_ui_model_command():
    _test_construct_ui_command(
        htypes.rc_constructors.ui_model_command_ctr, ui_command_ctr.construct_ui_model_command)


def _test_construct_univeral_ui_command(command_ctr_t, fn):
    module_res = make_module_res()
    name_to_res = {}
    fn(
        piece=command_ctr_t(
            name='sample_command',
            params=('piece', 'state'),
            ),
        custom_types=local_types,
        name_to_res=name_to_res,
        module_res=module_res,
        attr=make_inspect_attr(),
        )
    assert 'sample_command.universal_ui_command' in name_to_res


def test_construct_univeral_ui_command():
    _test_construct_univeral_ui_command(
        htypes.rc_constructors.universal_ui_command_ctr,
        ui_command_ctr.construct_universal_ui_command,
    )


def test_construct_univeral_ui_model_command():
    _test_construct_univeral_ui_command(
        htypes.rc_constructors.universal_ui_model_command_ctr,
        ui_command_ctr.construct_universal_ui_model_command,
    )
