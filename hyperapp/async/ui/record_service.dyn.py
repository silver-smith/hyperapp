from . import htypes
from .record import record_interface_ref
from .record_object import RecordObject


class RecordService(RecordObject):

    @classmethod
    async def from_piece(cls, piece, identity, mosaic, async_web, object_animator, command_registry, rpc_endpoint, async_rpc_proxy):
        object_type = await async_web.summon(piece.type_ref)
        interface_ref = record_interface_ref(mosaic, piece)
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
        param_list = [
            await async_web.summon(param.param_ref)
            for param in piece.param_list
            ]
        result = await proxy.get(*param_list)
        record = result.record
        fields = {
            name: getattr(record, name)
            for name in record._t.fields
            }
        self = cls(piece, object_type, proxy, command_list)
        await self.async_init(object_animator, fields)
        return self

    def __init__(self, service, object_type, proxy, command_list):
        super().__init__()
        self._service = service
        self._object_type = object_type
        self._proxy = proxy
        self._command_list = command_list

    @property
    def piece(self):
        return self._service

    @property
    def type(self):
        return self._object_type

    @property
    def title(self):
        return f"Record service: {self._service.object_id}"

    def get_all_command_list(self):
        return self._command_list
