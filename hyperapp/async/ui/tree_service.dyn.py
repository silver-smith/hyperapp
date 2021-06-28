from . import htypes
from .tree import tree_interface_ref
from .column import Column
from .tree_object import TreeObject


class TreeService(TreeObject):

    @classmethod
    async def from_piece(cls, piece, identity, mosaic, types, command_registry, rpc_endpoint, async_rpc_proxy):
        tree_ot = mosaic.resolve_ref(piece.type_ref).value
        interface_ref = tree_interface_ref(mosaic, tree_ot)
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
        return cls(mosaic, types, tree_ot, piece.peer_ref, piece.object_id, proxy, command_list)

    def __init__(self, mosaic, types, tree_ot, peer_ref, object_id, proxy, command_list):
        super().__init__()
        self._mosaic = mosaic
        self._tree_ot = tree_ot
        self._peer_ref = peer_ref
        self._object_id = object_id
        self._proxy = proxy
        self._command_list = command_list
        self._column_list = [
            Column(
                id=column.id,
                type=types.resolve(column.type_ref),
                is_key=(column.id == tree_ot.key_column_id),
                )
            for column in tree_ot.column_list
            ]

    @property
    def piece(self):
        tree_ot_ref = self._mosaic.put(self._tree_ot)
        command_ref_list = [
            self._mosaic.put(command.piece)
            for command in self._command_list
            ]
        return htypes.service.tree_service(
            type_ref=tree_ot_ref,
            peer_ref=self._peer_ref,
            object_id=self._object_id,
            param_type_list=[],
            param_list=[],
            command_ref_list=command_ref_list,
            )

    @property
    def type(self):
        return self._tree_ot

    @property
    def title(self):
        return f"Tree service: {self._object_id}"

    def get_all_command_list(self):
        return self._command_list

    @property
    def columns(self):
        return self._column_list

    async def fetch_items(self, path):
        result = await self._proxy.get(path)
        self._distribute_fetch_results(path, result.items)
