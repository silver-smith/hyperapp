import logging
import uuid

from . import htypes
from .column import Column
from .list_object import ListDiff
from .simple_list_object import SimpleListObject

log = logging.getLogger(__name__)


class LiveListService(SimpleListObject):

    @staticmethod
    async def summon_dir(async_web, dir):
        return [
            await async_web.summon(ref) for ref in dir
            ]

    @classmethod
    async def from_piece(
            cls,
            piece,
            mosaic,
            types,
            async_web,
            command_registry,
            peer_registry,
            identity,
            rpc_endpoint,
            servant_path_factory,
            servant_path_from_data,
            async_rpc_call,
            ):
        peer = peer_registry.invite(piece.peer_ref)
        servant_path = servant_path_from_data(piece.servant_path)
        rpc_call = async_rpc_call(rpc_endpoint, peer, servant_path, identity)

        dir_list = [
            await cls.summon_dir(async_web, dir)
            for dir in piece.dir_list
            ]
        command_list = [
            await command_registry.invite(ref)
            for ref in piece.command_ref_list
            ]
        servant_name = f'live_list_service_{uuid.uuid4()}'
        self = cls(
            mosaic,
            types,
            async_web,
            servant_path_factory,
            identity,
            peer,
            servant_path,
            rpc_call,
            dir_list,
            command_list,
            piece.key_column_id,
            piece.column_list,
            servant_name,
            )
        rpc_endpoint.register_servant(servant_name, self)
        return self

    def __init__(
            self,
            mosaic,
            types,
            async_web,
            servant_path_factory,
            identity,
            peer,
            servant_path,
            rpc_call,
            custom_dir_list,
            command_list,
            key_column_id,
            column_list,
            servant_name,
            ):
        super().__init__()
        self._mosaic = mosaic
        self._types = types
        self._async_web = async_web
        self._servant_path_factory = servant_path_factory
        self._identity = identity
        self._peer = peer
        self._servant_path = servant_path
        self._rpc_call = rpc_call
        self._custom_dir_list = custom_dir_list
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
        self._servant_name = servant_name

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
        return htypes.service.live_list_service(
            peer_ref=self._mosaic.put(self._peer.piece),
            servant_path=self._servant_path.as_data,
            dir_list=dir_list,
            command_ref_list=command_ref_list,
            key_column_id=self._key_column_id,
            column_list=column_list,
            )

    @property
    def title(self):
        return f"Live list service: {self._servant_path.title}"

    @property
    def dir_list(self):
        return super().dir_list + self._custom_dir_list

    @property
    def command_list(self):
        return self._rpc_command_list

    @property
    def columns(self):
        return self._column_list

    async def get_all_items(self):
        servant_path = self._servant_path_factory().registry_name(self._servant_name).get_attr('process_diff')
        my_peer_ref = self._mosaic.put(self._identity.peer.piece)
        return await self._rpc_call(my_peer_ref, servant_path.as_data)

    async def process_diff(self, request, diff):
        remove_item_list = [
            await self._async_web.summon(ref)
            for ref in diff.remove_key_list
            ]
        item_list = [
            await self._async_web.summon(ref)
            for ref in diff.item_list
            ]
        log.info("Process diff: -%s, +%s", remove_item_list, item_list)
        self._distribute_diff(ListDiff(remove_item_list, item_list))
