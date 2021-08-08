import logging

from hyperapp.common.module import Module

from . import htypes
from .object_command import Command

from . import htypes
from .object_command import BuiltinCommand, Command

log = logging.getLogger(__name__)


class AltBuiltinCommand:

    @classmethod
    async def from_piece(cls, piece, object_factory):
        object = await object_factory.invite(piece.object)
        method = getattr(object, piece.method_name)
        base_command = BuiltinCommand.from_method(object, method)
        return cls(object, base_command, piece.method_name)

    def __init__(self, object, base_command, method_name):
        self._object = object
        self._base_command = base_command
        self._method_name = method_name
        self.name = f"alt:{method_name}"

    def __repr__(self):
        return f"Alt:{self._base_command}"

    @property
    def dir(self):
        return [*self._base_command.dir, htypes.alt_command.alt_command_d()]

    async def run(self, object, view_state, origin_dir):
        return await self._base_command.run(object, view_state, origin_dir)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._mosaic = services.mosaic
        self._lcs = services.lcs

        services.command_registry.register_actor(
            htypes.alt_command.clone_command_command, Command.from_fn(self.name, self.clone_command))
        services.command_registry.register_actor(
            htypes.alt_command.alt_command, AltBuiltinCommand.from_piece, services.object_factory)
        services.lcs.add(
            [htypes.command_list.object_command_list_d(), htypes.command.object_commands_d()],
            htypes.alt_command.clone_command_command(),
            )

    async def clone_command(self, object, view_state, origin_dir):
        command = object.key_to_command(view_state.current_key)
        log.info("Clone command: %s", command)
        dir = object.target_object.dir_list[-1]
        piece_ref = self._mosaic.put(object.target_object.piece)
        self._lcs.add(
            [*dir, htypes.command.object_commands_d()],
            htypes.alt_command.alt_command(piece_ref, command.method_name),
            )
        await object.update()
