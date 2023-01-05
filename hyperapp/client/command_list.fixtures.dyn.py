from hyperapp.common.htypes import phony_ref

from .import htypes
from .services import (
    mark,
    mosaic,
    types,
    )
from .code.view_command import ViewCommand

_null_ref = phony_ref('null')


@mark.module.qt_keys.run_input_key_dialog
def run_input_key_dialog():
    return ''


def _phony_command():
    dir_t = htypes.command_list_fixtures.sample_global_command_d
    dir_t_ref = types.reverse_resolve(dir_t)
    dir_t_res = htypes.legacy_type.type(dir_t_ref)
    dir = htypes.call.call(mosaic.put(dir_t_res))
    return htypes.impl.global_command_impl(
        function=_null_ref,
        dir=mosaic.put(dir),
        )

@mark.service
def global_command_list():
    return [_phony_command()]


class _PhonyRootView:

    def iter_view_commands(self):
        command = ViewCommand(
            module_name='command_list.fixture',
            qual_name='phony.view.command',
            name='phony',
            method=None,
            )
        return [([], command)]


@mark.service
def root_view():
    return _PhonyRootView()


class PhonyItem:

    def __init__(self):
        dir = htypes.command_list_fixtures.phony_d()
        self.name = "Phony item"
        self.dir = mosaic.put(dir)


@mark.param.GlobalCommandList
def piece():
    return htypes.command_list.global_command_list()


@mark.param.GlobalCommandList.set_key
def current_item():
    return PhonyItem()


@mark.param.GlobalCommandList.set_key_escape
def current_item():
    return PhonyItem()


@mark.param.ViewCommandList
def piece():
    return htypes.command_list.view_command_list()


@mark.param.ViewCommandList.set_key
def current_item():
    return PhonyItem()


@mark.param.ViewCommandList.set_key_escape
def current_item():
    return PhonyItem()


@mark.service
async def adapter_factory():
    return None


class _PhonyObjectCommandsFactory:

    def enum_object_command_pieces(self, adapter):
        return [_phony_command()]


@mark.service
def object_commands_factory():
    return _PhonyObjectCommandsFactory()


@mark.param.ObjectCommandList
def piece():
    return htypes.command_list.object_command_list(
        piece_ref=mosaic.put(None),
        view_state_ref=mosaic.put(None),
        )


@mark.param.ObjectCommandList.set_key
def current_item():
    return PhonyItem()


@mark.param.ObjectCommandList.set_key_escape
def current_item():
    return PhonyItem()


@mark.param.open_object_commands
def piece():
    return None


@mark.param.open_object_commands
def view_state():
    return None
