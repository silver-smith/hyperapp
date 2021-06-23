from hyperapp.common.module import Module

from . import htypes


class ObjectCommandsFactory:

    def __init__(self, lcs, command_registry):
        self._lcs = lcs
        self._command_registry = command_registry

    async def get_object_command_list(self, object):
        command_ref_it = self._lcs.iter(
            [[*dir, htypes.command.object_commands_d] for dir in object.dir_list]
            )
        command_list = [
            await self._command_registry.invite(ref)
            for ref in command_ref_it
            ]
        return [
            *object.command_list,
            *command_list,
            ]


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.object_commands_factory = ObjectCommandsFactory(services.lcs, services.command_registry)
