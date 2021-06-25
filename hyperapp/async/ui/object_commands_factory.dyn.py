from hyperapp.common.module import Module

from . import htypes


class ObjectCommandsFactory:

    def __init__(self, mosaic, lcs, command_registry):
        self._lcs = lcs
        self._command_registry = command_registry
        self._object_commands_d_ref = mosaic.put(htypes.command.object_commands_d())

    async def get_object_command_list(self, object):
        command_piece_it = self._lcs.iter(
            [[*dir, self._object_commands_d_ref] for dir in object.dir_list]
            )
        command_list = [
            await self._command_registry.animate(piece)
            for piece in command_piece_it
            ]
        return [
            *object.command_list,
            *command_list,
            ]


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.object_commands_factory = ObjectCommandsFactory(
            services.mosaic, services.lcs, services.command_registry)
