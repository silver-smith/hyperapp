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


def global_command_list():
    dir_t = htypes.command_list_fixtures.sample_global_command_d
    dir_t_ref = types.reverse_resolve(dir_t)
    dir_t_res = htypes.legacy_type.type(dir_t_ref)
    dir = htypes.call.call(mosaic.put(dir_t_res))
    command = htypes.impl.global_command_impl(
        function=_null_ref,
        dir=mosaic.put(dir),
        )
    return [command]


class _PhonyRootView:

    def iter_view_commands(self):
        command = ViewCommand(
            module_name='command_list.fixture',
            qual_name='phony.view.command',
            name='phony',
            method=None,
            )
        return [([], command)]


service.root_view = _PhonyRootView()

param.GlobalCommandList.piece = htypes.command_list.global_command_list()
param.GlobalCommandList.set_key.current_item = None

param.ViewCommandList.piece = htypes.command_list.view_command_list()

param.ObjectCommandList.piece = htypes.command_list.object_command_list(
    piece_ref=mosaic.put(None),
    view_state_ref=mosaic.put(None),
    )

param.object_commands.piece = None
param.object_commands.view_state = None
