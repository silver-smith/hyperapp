from . import htypes
from .object_command import Command
from .module import ClientModule


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.lcs.add(
            [htypes.object.object_d(), htypes.command.object_commands_d()],
            htypes.raw_piece.raw_piece_command(),
            )
        services.command_registry.register_actor(
            htypes.raw_piece.raw_piece_command, Command.from_fn(self.name, self.open_raw_piece), services.mosaic)

    async def open_raw_piece(self, object, view_state, origin_dir, mosaic):
        return htypes.data_viewer.data_viewer(
            data_ref=mosaic.put(object.piece),
            )
