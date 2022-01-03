from . import htypes
from .record_object import RecordObject


class RecordService(RecordObject):

    @staticmethod
    async def summon_dir(async_web, dir):
        return [
            await async_web.summon(ref) for ref in dir
            ]

    @classmethod
    async def from_piece(
            cls, piece,
            mosaic, async_web, object_factory, command_registry, peer_registry,
            identity, rpc_endpoint, async_rpc_call_factory):

        peer = peer_registry.invite(piece.peer_ref)
        rpc_call = async_rpc_call_factory(rpc_endpoint, peer, piece.servant_fn_ref, identity)

        dir_list = [
            await cls.summon_dir(async_web, dir)
            for dir in piece.dir_list
            ]
        command_list = [
            await command_registry.invite(ref)
            for ref in piece.command_ref_list
            ]
        record = await rpc_call()
        fields_pieces = {
            name: getattr(record, name)
            for name in record._t.fields
            }
        self = cls(mosaic, peer, piece.servant_fn_ref, dir_list, command_list)
        await self.async_init(object_factory, fields_pieces)
        return self

    def __init__(self, mosaic, peer, servant_fn_ref, custom_dir_list, command_list):
        super().__init__()
        self._mosaic = mosaic
        self._peer = peer
        self._servant_fn_ref = servant_fn_ref
        self._custom_dir_list = custom_dir_list
        self._rpc_command_list = command_list

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
        return htypes.service.record_service(
            peer_ref=self._mosaic.put(self._peer.piece),
            servant_fn_ref=self._servant_fn_ref,
            dir_list=dir_list,
            command_ref_list=command_ref_list,
            )

    @property
    def title(self):
        return f"Record service: {self._servant_fn_ref}"

    @property
    def dir_list(self):
        return super().dir_list + self._custom_dir_list

    def get_command_list(self):
        return self._rpc_command_list
