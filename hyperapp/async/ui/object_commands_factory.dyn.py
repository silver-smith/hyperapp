from hyperapp.common.module import Module

from . import htypes


class ObjectCommandsFactory:

    def __init__(self, mosaic, lcs, adapter_factory):
        self._lcs = lcs
        self._adapter_factory = adapter_factory

    async def make_commands(self, piece, adapter, view):
        command_impl_it = self._lcs.iter_dir_list_values(
            [[*dir, htypes.command.object_commands_d()] for dir in adapter.dir_list]
            )
        command_list = [
            await self._adapter_factory(piece)
            for impl in command_impl_it
            ]
        return [
            *object.command_list,
            *command_list,
            ]

    async def command_by_name(self, object, name):
        for command in await self.get_object_command_list(object):
            if command.name == name:
                return command
        raise KeyError(name)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.object_commands_factory = ObjectCommandsFactory(
            services.mosaic, services.lcs, services.adapter_factory)
