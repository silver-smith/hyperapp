from collections import namedtuple
from datetime import datetime

from dateutil.tz import tzlocal

from . import htypes
from .command import command
from .column import Column
from .list_object import ListDiff
from .simple_list_object import SimpleListObject
from .module import ClientModule


Item = namedtuple('Item', 'at roots')


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
            Column('at', is_key=True),
            Column('roots'),
            ]

    async def get_all_items(self):
        return []

    def _on_request(self, request):
        item = Item(
            at=datetime.now(tzlocal()),
            roots=request.ref_list,
            )
        self._distribute_diff(ListDiff.add_one(item))

    # @command
    # async def open(self, current_key):
    #     item = self._name_to_item[current_key]
    #     return htypes.data_viewer.data_viewer(item.module_ref)


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
