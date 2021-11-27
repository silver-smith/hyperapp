from . import htypes
from .tree_object import TreeObject


class TreeService(TreeObject):

    @staticmethod
    async def summon_dir(async_web, dir):
        return [
            await async_web.summon(ref) for ref in dir
            ]

    @classmethod
    async def from_piece(
            cls, piece,
            mosaic, types, async_web, command_registry, peer_registry,
            identity, rpc_endpoint, servant_path_from_data, async_rpc_call_factory):

        peer = peer_registry.invite(piece.peer_ref)
        servant_path = servant_path_from_data(piece.servant_path)
        rpc_call = async_rpc_call_factory(rpc_endpoint, peer, servant_path, identity)

        dir_list = [
            await cls.summon_dir(async_web, dir)
            for dir in piece.dir_list
            ]
        command_list = [
            await command_registry.invite(ref)
            for ref in piece.command_ref_list
            ]
        return cls(mosaic, types, peer, servant_path, rpc_call, dir_list, command_list, piece.key_attribute)

    def __init__(self, mosaic, types, peer, servant_path, rpc_call, custom_dir_list, command_list, key_attribute):
        super().__init__()
        self._mosaic = mosaic
        self._types = types
        self._peer = peer
        self._servant_path = servant_path
        self._rpc_call = rpc_call
        self._custom_dir_list = custom_dir_list
        self._rpc_command_list = command_list
        self._key_attribute = key_attribute

    @property
    def piece(self):
        dir_list = [
            [self._mosaic.put(ref) for ref in dir]
            for dir in self._custom_dir_list
            ]
        command_ref_list = [
            self._mosaic.put(command.piece)
            for command in self._rpc_command_list
            ]
        return htypes.service.tree_service(
            peer_ref=self._mosaic.put(self._peer.piece),
            servant_path=self._servant_path.as_data,
            dir_list=dir_list,
            command_ref_list=command_ref_list,
            key_attribute=self._key_attribute,
            )

    @property
    def title(self):
        return f"Tree service: {self._servant_path.title}"

    @property
    def dir_list(self):
        return super().dir_list + self._custom_dir_list

    @property
    def command_list(self):
        return self._rpc_command_list

    @property
    def key_attribute(self):
        return self._key_attribute

    async def fetch_items(self, path):
        items = await self._rpc_call(path)
        self._distribute_fetch_results(path, items)
