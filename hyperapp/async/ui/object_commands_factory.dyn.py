from hyperapp.common.module import Module

from . import htypes


class ObjectCommandsFactory:

    def __init__(self, mosaic, lcs, command_registry):
        self._lcs = lcs
        self._command_registry = command_registry

    def enum_object_command_pieces(self, adapter):
        return self._lcs.iter_dir_list_values(
            [[*dir, htypes.command.object_commands_d()] for dir in [[], *adapter.dir_list]]
            )

    async def get_object_command_list(self, navigator, object_piece, adapter, view):
        command_piece_it = self.enum_object_command_pieces(adapter)
        return [
            await self.command_from_piece(command_piece, navigator, object_piece, adapter, view)
            for command_piece in command_piece_it
            ]

    async def command_from_piece(self, command_piece, navigator, object_piece, adapter, view):
        return await self._command_registry.animate(command_piece, navigator, object_piece, adapter, view)

    async def command_by_name(self, object, name):
        for command in await self.get_object_command_list(object):
            if command.name == name:
                return command
        raise KeyError(name)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.object_commands_factory = ObjectCommandsFactory(
            services.mosaic, services.lcs, services.command_registry)
