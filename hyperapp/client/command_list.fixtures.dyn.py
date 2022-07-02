from hyperapp.common.htypes import phony_ref

from .import htypes
from .services import (
    mosaic,
    types,
    )
from .view_command import ViewCommand


_null_ref = phony_ref('null')


def global_command_list_piece():
    return htypes.command_list.global_command_list()


def view_command_list_piece():
    return htypes.command_list.view_command_list()


def global_command_list_global_command_list():
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


def view_command_list_root_view():
    return _PhonyRootView()
