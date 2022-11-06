from hyperapp.common.htypes import phony_ref

from . import htypes
from .services import (
    mosaic,
    resource_module_registry,
    types,
    )
from .marker import param
from .service_decorator import service


function_res = resource_module_registry['server.server_global_commands.fixtures.aux']['sample_function']


def _phony_global_command():
    dir_t = htypes.server_global_commands_fixtures.sample_global_command_d
    dir_t_ref = types.reverse_resolve(dir_t)
    dir_t_res = htypes.legacy_type.type(dir_t_ref)
    dir = htypes.call.call(mosaic.put(dir_t_res))
    return htypes.impl.global_command_impl(
        function=mosaic.put(function_res),
        dir=mosaic.put(dir),
        )


service.global_command_list = [
    _phony_global_command(),
    ]

param.ServerGlobalCommands.piece = htypes.server_global_commands.server_global_commands()
param.ServerGlobalCommands.run.current_key = 'sample_global_command'

param.global_command_to_item.piece = _phony_global_command()
