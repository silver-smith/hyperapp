from . import htypes
from .tree import tree_interface_ref
from .column import Column
from .tree_object import TreeObject


class TreeService(TreeObject):

    @staticmethod
    async def summon_dir(async_web, dir):
        return [
            await async_web.summon(ref) for ref in dir
            ]

    @classmethod
    async def from_piece(cls, piece, identity, mosaic, types, async_web, command_registry, rpc_endpoint, async_rpc_proxy):
        dir_list = [
            await cls.summon_dir(async_web, dir)
            for dir in piece.dir_list
            ]
        interface_ref = tree_interface_ref(mosaic, piece)
        service = htypes.rpc.endpoint(
            peer_ref=piece.peer_ref,
            iface_ref=interface_ref,
            object_id=piece.object_id,
            )
        proxy = async_rpc_proxy(identity, rpc_endpoint, service)
        command_list = [
            await command_registry.invite(ref)
            for ref in piece.command_ref_list
            ]
        return cls(mosaic, types, piece.peer_ref, piece.object_id, dir_list, piece.key_column_id, piece.column_list, proxy, command_list)

    def __init__(self, mosaic, types, peer_ref, object_id, custom_dir_list, key_column_id, column_list, proxy, command_list):
        super().__init__()
        self._mosaic = mosaic
        self._types = types
        self._peer_ref = peer_ref
        self._object_id = object_id
        self._custom_dir_list = custom_dir_list
        self._proxy = proxy
        self._rpc_command_list = command_list
        self._key_column_id = key_column_id
        self._column_list = [
            Column(
                id=column.id,
                type=types.resolve(column.type_ref),
                is_key=(column.id == key_column_id),
                )
            for column in column_list
            ]

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
        column_list = [
            htypes.service.column(column.id, self._types.reverse_resolve(column.type))
            for column in self._column_list
            ]
        return htypes.service.tree_service(
            peer_ref=self._peer_ref,
            object_id=self._object_id,
            dir_list=dir_list,
            param_type_list=[],
            param_list=[],
            command_ref_list=command_ref_list,
            key_column_id=self._key_column_id,
            column_list=column_list,
            )

    @property
    def title(self):
        return f"Tree service: {self._object_id}"

    @property
    def dir_list(self):
        return super().dir_list + self._custom_dir_list

    @property
    def command_list(self):
        return self._rpc_command_list

    @property
    def columns(self):
        return self._column_list

    async def fetch_items(self, path):
        result = await self._proxy.get(path)
        self._distribute_fetch_results(path, result.items)
