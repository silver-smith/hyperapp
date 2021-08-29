import logging

from hyperapp.common.module import Module

from . import htypes
from .object_command import Command

log = logging.getLogger(__name__)


def open_view_config(object, view_dir_to_config):
    for dir in object.dir_list:
        try:
            config_editor_factory = view_dir_to_config[tuple(dir)]
        except KeyError:
            continue
        else:
            return config_editor_factory(object)
    raise RuntimeError(f"No view config editor is registered for any of object {object} dirs: {object.dir_list}")

    
class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.view_dir_to_config = {}

        services.command_registry.register_actor(
            htypes.view_config.open_view_config_command, Command.from_fn(self.name, open_view_config), services.view_dir_to_config)
        services.lcs.add(
            [htypes.object.object_d(), htypes.command.object_commands_d()],
            htypes.view_config.open_view_config_command(),
            )
