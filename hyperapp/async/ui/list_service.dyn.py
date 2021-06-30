from . import htypes
from .list import list_interface_ref
from .column import Column
from .simple_list_object import SimpleListObject


class ListService(SimpleListObject):

    @classmethod
    async def from_piece(cls, piece, identity, mosaic, types, command_registry, rpc_endpoint, async_rpc_proxy):
        interface_ref = list_interface_ref(mosaic, piece)
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
        return cls(mosaic, types, piece.peer_ref, piece.object_id, piece.key_column_id, piece.column_list, proxy, command_list)

    def __init__(self, mosaic, types, peer_ref, object_id, key_column_id, column_list, proxy, command_list):
        super().__init__()
        self._mosaic = mosaic
        self._types = types
        self._peer_ref = peer_ref
        self._object_id = object_id
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
        command_ref_list = [
            self._mosaic.put(command.piece)
            for command in self._rpc_command_list
            ]
        column_list = [
            htypes.service.column(column.id, self._types.reverse_resolve(column.type))
            for column in self._column_list
            ]
        return htypes.service.list_service(
            peer_ref=self._peer_ref,
            object_id=self._object_id,
            param_type_list=[],
            param_list=[],
            command_ref_list=command_ref_list,
            key_column_id=self._key_column_id,
            column_list=column_list,
            )

    @property
    def title(self):
        return f"List service: {self._object_id}"

    @property
    def command_list(self):
        return self._rpc_command_list

    @property
    def columns(self):
        return self._column_list

    async def get_all_items(self):
        result = await self._proxy.get()
        return [row for row in result.rows]
