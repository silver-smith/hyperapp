from . import htypes
from .record import record_interface_ref
from .record_object import RecordObject


class RecordService(RecordObject):

    @staticmethod
    async def summon_dir(async_web, dir):
        return [
            await async_web.summon(ref) for ref in dir
            ]

    @classmethod
    async def from_piece(cls, piece, identity, mosaic, async_web, object_factory, command_registry, rpc_endpoint, async_rpc_proxy):
        dir_list = [
            await cls.summon_dir(async_web, dir)
            for dir in piece.dir_list
            ]
        interface_ref = record_interface_ref(mosaic, piece)
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
        self = cls(piece, dir_list, proxy, command_list)
        await self.async_init(object_factory, fields)
        return self

    def __init__(self, service, custom_dir_list, proxy, command_list):
        super().__init__()
        self._service = service
        self._custom_dir_list = custom_dir_list
        self._proxy = proxy
        self._command_list = command_list

    @property
    def piece(self):
        return self._service

    @property
    def title(self):
        return f"Record service: {self._service.object_id}"

    @property
    def dir_list(self):
        return super().dir_list + self._custom_dir_list

    def get_command_list(self):
        return self._command_list
