from hyperapp.common.htypes import phony_ref

from .import htypes
from .services import (
    mosaic,
    types,
    )
from .view_command import ViewCommand
from .marker import module, param, service

_null_ref = phony_ref('null')


@module.qt_keys.run_input_key_dialog
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

@service
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


@service
def root_view():
    return _PhonyRootView()


class PhonyItem:

    def __init__(self):
        dir = htypes.command_list_fixtures.phony_d()
        self.name = "Phony item"
        self.dir = mosaic.put(dir)


@param.GlobalCommandList
def piece():
    return htypes.command_list.global_command_list()


@param.GlobalCommandList.set_key
def current_item():
    return PhonyItem()


@param.GlobalCommandList.set_key_escape
def current_item():
    return PhonyItem()


param.ViewCommandList.piece = htypes.command_list.view_command_list()


@param.ViewCommandList.set_key
def current_item():
    return PhonyItem()


@param.ViewCommandList.set_key_escape
def current_item():
    return PhonyItem()


@service.adapter_factory
async def phony_adapter_factory(piece):
    return None


class _PhonyObjectCommandsFactory:

    def enum_object_command_pieces(self, adapter):
        return [_phony_command()]


@service
def object_commands_factory():
    return _PhonyObjectCommandsFactory()


@param.ObjectCommandList
def piece():
    return htypes.command_list.object_command_list(
        piece_ref=mosaic.put(None),
        view_state_ref=mosaic.put(None),
        )


@param.ObjectCommandList.set_key
def current_item():
    return PhonyItem()


@param.ObjectCommandList.set_key_escape
def current_item():
    return PhonyItem()


param.open_object_commands.piece = None
param.open_object_commands.view_state = None
