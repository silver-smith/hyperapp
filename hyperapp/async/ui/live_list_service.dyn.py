import logging
import weakref
import uuid

from . import htypes
from .list_object import ListDiff
from .simple_list_object import SimpleListObject

log = logging.getLogger(__name__)


class LiveListService(SimpleListObject):

    _piece_to_instance = weakref.WeakValueDictionary()

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
            async_rpc_call_factory,
            ):

        try:
            return cls._piece_to_instance[piece]
        except KeyError:
            pass
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
        self = cls(
            mosaic,
            types,
            async_web,
            identity,
            peer,
            piece.servant_fn_ref,
            rpc_call,
            dir_list,
            command_list,
            piece.key_attribute,
            )
        cls._piece_to_instance[piece] = self
        return self

    def __init__(
            self,
            mosaic,
            types,
            async_web,
            identity,
            peer,
            servant_fn_ref,
            rpc_call,
            custom_dir_list,
            command_list,
            key_attribute,
            ):
        super().__init__()
        self._mosaic = mosaic
        self._types = types
        self._async_web = async_web
        self._identity = identity
        self._peer = peer
        self._servant_fn_ref = servant_fn_ref
        self._rpc_call = rpc_call
        self._custom_dir_list = custom_dir_list
        self._rpc_command_list = command_list
        self._key_attribute = key_attribute

    @property
    def piece(self):
        dir_list = tuple(
            tuple(self._mosaic.put(ref) for ref in dir)
            for dir in self._custom_dir_list
            )
        command_ref_list = tuple(
            self._mosaic.put(command.piece)
            for command in self._rpc_command_list
            )
        return htypes.service.live_list_service(
            peer_ref=self._mosaic.put(self._peer.piece),
            servant_fn_ref=self._servant_fn_ref,
            dir_list=dir_list,
            command_ref_list=command_ref_list,
            key_attribute=self._key_attribute,
            )

    @property
    def title(self):
        return f"Live list service: {self._servant_fn_ref}"

    @property
    def dir_list(self):
        return super().dir_list + self._custom_dir_list

    @property
    def command_list(self):
        return self._rpc_command_list

    @property
    def key_attribute(self):
        return self._key_attribute

    async def get_all_items(self):
        diff_method_piece = htypes.attribute.attribute(
            object=self._mosaic.put(self.piece),
            attr_name='process_diff',
            )
        servant_ref = self._mosaic.put(diff_method_piece)
        my_peer_ref = self._mosaic.put(self._identity.peer.piece)
        return await self._rpc_call(my_peer_ref, servant_ref)

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
