import asyncio

from hyperapp.common.module import Module

from . import htypes


def register_global_command(piece, web, event_loop_holder, command_hub_list, global_command_list):
    command = web.summon(piece.command)
    global_command_list.append(command)
    event_loop_holder.create_task_if_started(command_hub_list.update())


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.global_command_list = []
        services.meta_registry.register_actor(
            htypes.global_command.global_command_association,
            register_global_command,
            services.web,
            services.event_loop_holder,
            services.command_hub_list,
            services.global_command_list,
            )
