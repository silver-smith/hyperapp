import logging

from hyperapp.common.module import Module

from . import htypes
from .object_command import Command

log = logging.getLogger(__name__)


def open_view_config(piece):
    assert 0, 'todo'

    
class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.command_registry.register_actor(
            htypes.view_config.open_view_config_command, Command.from_fn(self.name, open_view_config))
        services.lcs.add(
            [htypes.object.object_d(), htypes.command.object_commands_d()],
            htypes.view_config.open_view_config_command(),
            )
