from . import htypes
from .services import (
    local_types,
    mark,
    mosaic,
    pyobj_creg,
    )
from .tested.code import ui_command_ctr


def test_construct_ui_command():
    module_res = htypes.builtin.python_module(
        module_name='ui_command_ctr_tests',
        source='',
        file_path='/ui_command_ctr_tests.dyn.py',
        import_list=(),
        )
    string_res = pyobj_creg.reverse_resolve(htypes.builtin.string)
    name_to_res = {}
    ui_command_ctr.construct_ui_command(
        piece=htypes.attr_constructors.ui_command_ctr(
            t=mosaic.put(string_res),
            params=('piece', 'state'),
            ),
        custom_types=local_types,
        name_to_res=name_to_res,
        module_res=module_res,
        attr=htypes.inspect.attr(
            name='sample_command',
            module=None,
            resource_name=None,
            constructors=(),
            ),
        )
    assert 'sample_command.ui_command' in name_to_res


def test_construct_univeral_ui_command():
    module_res = htypes.builtin.python_module(
        module_name='ui_command_ctr_tests',
        source='',
        file_path='/ui_command_ctr_tests.py',
        import_list=(),
        )
    name_to_res = {}
    ui_command_ctr.construct_universal_ui_command(
        piece=htypes.attr_constructors.universal_ui_command_ctr(
            params=('piece', 'state'),
            ),
        custom_types=local_types,
        name_to_res=name_to_res,
        module_res=module_res,
        attr=htypes.inspect.attr(
            name='sample_command',
            module=None,
            resource_name=None,
            constructors=(),
            ),
        )
    assert 'sample_command.ui_command' in name_to_res
