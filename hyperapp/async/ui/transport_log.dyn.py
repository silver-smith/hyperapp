import itertools
import weakref
from collections import namedtuple
from datetime import datetime

from dateutil.tz import tzlocal

from hyperapp.common.htypes import tInt

from . import htypes
from .command import command
from .list_object import ListDiff
from .simple_list_object import SimpleListObject
from .module import ClientModule


MESSAGE_LIMIT = 10

Item = namedtuple('Item', 'id at direction refs')


class TransportLog(SimpleListObject):

    dir_list = [
        *SimpleListObject.dir_list,
        [htypes.transport_log.transport_log_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, item_list, id_to_ref_list):
        self = this_module._transport_log_object_wr()
        if self:
            return self
        self = cls(item_list, id_to_ref_list)
        this_module._transport_log_object_wr = weakref.ref(self)
        return self
        
    def __init__(self, item_list, id_to_ref_list):
        super().__init__()
        self._item_list = item_list
        self._id_to_ref_list = id_to_ref_list

    @property
    def piece(self):
        return htypes.transport_log.transport_log()

    @property
    def title(self):
        return f"Transport log"

    @property
    def key_attribute(self):
        return 'id'

    async def get_all_items(self):
        return self._item_list

    @command
    async def open(self, current_key):
        ref_list = self._id_to_ref_list[current_key]
        [first_ref, *rest] = ref_list
        assert not rest  # todo: open when there is more than one root in single request.
        return htypes.data_viewer.data_viewer(first_ref)


class ThisModule(ClientModule):

    class _Phony:
        pass

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._web = services.web
        self._item_list = []
        self._id_to_ref_list = {}
        self._id_counter = itertools.count()
        self._transport_log_object_wr = weakref.ref(self._Phony())  # Create dead ref to avoid checking _wr for None.

        services.object_registry.register_actor(
            htypes.transport_log.transport_log,
            TransportLog.from_piece,
            self._item_list,
            self._id_to_ref_list,
            )
        services.transport_log_callback_registry.add(self._on_request)

    def _on_request(self, direction, ref_list):
        refs_str = ', '.join(
            str(self._web.summon(ref))
            for ref in ref_list
            )
        item = Item(
            id=next(self._id_counter),
            at=datetime.now(tzlocal()),
            direction=direction,
            refs=refs_str,
            )
        self._item_list.append(item)
        if len(self._item_list) > MESSAGE_LIMIT:
            self._item_list = self._item_list[-MESSAGE_LIMIT:]
        self._id_to_ref_list[item.id] = ref_list
        object = self._transport_log_object_wr()
        if object:
            object._distribute_diff(ListDiff.add_one(item))

    @command
    async def transport_log(self):
        return htypes.transport_log.transport_log()
