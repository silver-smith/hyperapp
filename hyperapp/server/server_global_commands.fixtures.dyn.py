from hyperapp.common.htypes import phony_ref

from . import htypes
from .services import (
    mosaic,
    resource_registry,
    types,
    )
from .marker import param, service




def _phony_global_command():
    function_res = resource_registry['server.server_global_commands.fixtures.aux', 'sample_function']
    dir_t = htypes.server_global_commands_fixtures.sample_global_command_d
    dir = dir_t()
    return htypes.impl.global_command_impl(
        function=mosaic.put(function_res),
        dir=mosaic.put(dir),
        )


@service
def global_command_list():
    return [
        _phony_global_command(),
        ]


param.ServerGlobalCommands.piece = htypes.server_global_commands.server_global_commands()
param.ServerGlobalCommands.run.current_key = 'sample_global_command'


@param.global_command_to_item
def piece():
    return _phony_global_command()
