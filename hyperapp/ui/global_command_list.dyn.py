from hyperapp.common.module import Module

from . import htypes


def register_global_command(piece, web, global_command_list):
    command = web.summon(piece.command)
    global_command_list.append(command)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.global_command_list = []
        services.meta_registry.register_actor(
            htypes.global_command.global_command_association, register_global_command, services.web, services.global_command_list)
