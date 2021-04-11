from hyperapp.common.htypes import list_service_t

from . import htypes
from .list_object import list_interface_ref
from .column import Column
from .simple_list_object import SimpleListObject


class ListService(SimpleListObject):

    @classmethod
    async def from_piece(cls, piece, identity, mosaic, types, rpc_endpoint, async_rpc_proxy):
        list_ot = mosaic.resolve_ref(piece.type_ref).value
        interface_ref = list_interface_ref(mosaic, list_ot, 'test_list_service')
        service = htypes.rpc.endpoint(
            peer_ref=piece.peer_ref,
            iface_ref=interface_ref,
            object_id=piece.object_id,
            )
        proxy = async_rpc_proxy(identity, rpc_endpoint, service)
        return cls(mosaic, types, list_ot, piece.peer_ref, piece.object_id, proxy)

    def __init__(self, mosaic, types, list_ot, peer_ref, object_id, proxy):
        super().__init__()
        self._mosaic = mosaic
        self._list_ot = list_ot
        self._peer_ref = peer_ref
        self._object_id = object_id
        self._proxy = proxy
        self._columns = [
            Column(
                id=column.id,
                type=types.resolve(column.type_ref),
                is_key=(column.id == list_ot.key_column_id),
                )
            for column in list_ot.column_list
            ]

    @property
    def title(self):
        return f"List service: {self._object_id}"

    @property
    def piece(self):
        list_ot_ref = self._mosaic.put(self._list_ot)
        return list_service_t(
            type_ref=list_ot_ref,
            peer_ref=self._peer_ref,
            object_id=self._object_id,
            key_field=self._key_field,
            )

    @property
    def columns(self):
        return self._columns

    async def get_all_items(self):
        row_list = await self._proxy.get()
        return [row for row in row_list]
