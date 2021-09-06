import itertools
from collections import namedtuple
from datetime import datetime

from dateutil.tz import tzlocal

from hyperapp.common.htypes import tInt

from . import htypes
from .command import command
from .column import Column
from .list_object import ListDiff
from .simple_list_object import SimpleListObject
from .module import ClientModule


Item = namedtuple('Item', 'id at roots')


class TransportLog(SimpleListObject):

    dir_list = [
        *SimpleListObject.dir_list,
        [htypes.transport_log.transport_log_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, web, transport_log_callback_registry):
        return cls(web, transport_log_callback_registry)
        
    def __init__(self, web, transport_log_callback_registry):
        super().__init__()
        self._web = web
        self._id_counter = itertools.count()
        self._id_to_ref_list = {}
        transport_log_callback_registry.add(self._on_request)

    @property
    def piece(self):
        return htypes.transport_log.transport_log()

    @property
    def title(self):
        return f"Transport log"

    @property
    def columns(self):
        return [
            Column('id', type=tInt, is_key=True),
            Column('at'),
            Column('roots'),
            ]

    async def get_all_items(self):
        return []

    def _on_request(self, request):
        roots = ', '.join(
            str(self._web.summon(ref))
            for ref in request.ref_list
            )
        item = Item(
            id=next(self._id_counter),
            at=datetime.now(tzlocal()),
            roots=roots,
            )
        self._id_to_ref_list[item.id] = request.ref_list
        self._distribute_diff(ListDiff.add_one(item))

    @command
    async def open(self, current_key):
        ref_list = self._id_to_ref_list[current_key]
        [first_ref, *rest] = ref_list
        assert not rest  # todo: open when there is more than one root in single request.
        return htypes.data_viewer.data_viewer(first_ref)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.object_registry.register_actor(
            htypes.transport_log.transport_log,
            TransportLog.from_piece,
            services.web,
            services.transport_log_callback_registry,
            )

    @command
    async def transport_log(self):
        return htypes.transport_log.transport_log()
