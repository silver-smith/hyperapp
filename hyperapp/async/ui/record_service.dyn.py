from hyperapp.common.htypes import record_field_t, record_service_t

from . import htypes
from .record import record_interface_ref
from .record_object import RecordObject


class RecordService(RecordObject):

    @classmethod
    async def from_piece(cls, piece, identity, mosaic, object_animator, command_registry, rpc_endpoint, async_rpc_proxy):
        object_type = mosaic.resolve_ref(piece.type_ref).value
        interface_ref = record_interface_ref(mosaic, piece.field_list)
        service = htypes.rpc.endpoint(
            peer_ref=piece.peer_ref,
            iface_ref=interface_ref,
            object_id=piece.object_id,
            )
        proxy = async_rpc_proxy(identity, rpc_endpoint, service)
        command_list = [
            await command_registry.invite(rec.command_ref, rec.id)
            for rec in piece.command_list
            ]
        result = await proxy.get()
        record = result.record
        fields = {
            name: getattr(record, name)
            for name in record._t.fields
            }
        self = cls(mosaic, object_type, piece.peer_ref, piece.object_id, proxy, command_list, piece.field_list)
        await self.async_init(object_animator, fields)
        return self

    def __init__(self, mosaic, object_type, peer_ref, object_id, proxy, command_list, field_list):
        super().__init__()
        self._mosaic = mosaic
        self._object_type = object_type
        self._peer_ref = peer_ref
        self._object_id = object_id
        self._proxy = proxy
        self._command_list = command_list
        self._field_list = field_list
        self._fields = None

    @property
    def piece(self):
        object_type_ref = self._mosaic.put(self._object_type)
        command_list = [
            service_command_t(command.id, self._mosaic.put(command.piece))
            for command in self._command_list
            ]
        return record_service_t(
            type_ref=object_type_ref,
            peer_ref=self._peer_ref,
            object_id=self._object_id,
            command_list=command_list,
            field_list=self._field_list,
            )

    @property
    def type(self):
        return self._object_type

    @property
    def title(self):
        return f"Record service: {self._object_id}"

    def get_all_command_list(self):
        return self._command_list
