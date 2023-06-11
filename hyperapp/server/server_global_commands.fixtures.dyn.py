from hyperapp.common.htypes import phony_ref

from . import htypes
from .services import (
    mark,
    mosaic,
    resource_registry,
    types,
    )


def _sample_fn():
    pass


def _phony_global_command():
    this_module_res = resource_registry['server.server_global_commands.fixtures', 'server_global_commands.fixtures.module']
    fn_res = htypes.builtin.attribute(
        object=mosaic.put(this_module_res),
        attr_name='_sample_fn',
        )
    dir_t = htypes.server_global_commands_fixtures.sample_global_command_d
    dir = dir_t()
    return htypes.impl.global_command_impl(
        function=mosaic.put(fn_res),
        dir=mosaic.put(dir),
        )


@mark.service
def global_command_list():
    return [
        _phony_global_command(),
        ]


@mark.param.ServerGlobalCommands
def piece():
    return htypes.server_global_commands.server_global_commands()


@mark.param.ServerGlobalCommands.run
def current_key():
    return 'sample_global_command'


@mark.param.global_command_to_item
def piece():
    return _phony_global_command()
