import itertools
import logging
from collections import namedtuple

from hyperapp.common.htypes import tInt
from hyperapp.common.module import Module

from . import htypes
from .simple_list_object import SimpleListObject

log = logging.getLogger(__name__)


Item = namedtuple('Item', 'id dir_title type view view_title')


class AvailableViewList(SimpleListObject):

    dir_list = [
        *SimpleListObject.dir_list,
        [htypes.available_view_list.available_view_list_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, mosaic, web, object_factory, view_factory_registry, available_view_registry):
        object = await object_factory.invite(piece.piece_ref)
        self = cls(mosaic, web, view_factory_registry, available_view_registry, object)
        await self._async_init()
        return self

    def __init__(self, mosaic, web, view_factory_registry, available_view_registry, object):
        super().__init__()
        self._mosaic = mosaic
        self._web = web
        self._view_factory_registry = view_factory_registry
        self._available_view_registry = available_view_registry
        self._object = object
        self._item_list = None

    async def _async_init(self):
        self._item_list = await self._collect_items()

    async def _collect_items(self):
        item_list = []
        id_it = itertools.count()
        for dir in self._object.dir_list:
            dir_title = '/'.join(str(element) for element in dir)
            got_some = False
            for factory_piece in self._available_view_registry.list_dir(dir):
                if self._available_view_registry.is_fixed_factory(factory_piece):
                    type = 'fixed'
                else:
                    type = 'factory'
                view_piece = await self._view_factory_registry.animate(factory_piece, self._object)
                view_title = str(view_piece)
                item_list.append(Item(next(id_it), dir_title, type, view_piece, view_title))
                got_some = True
            if not got_some:
                item_list.append(Item(next(id_it), dir_title, None, None, '(no views available)'))
        return item_list

    @property
    def piece(self):
        piece_ref = self._mosaic.put(self._object.piece)
        return htypes.available_view_list.available_view_list(piece_ref)

    @property
    def title(self):
        return f"Available views for: {self._object.title}"

    @property
    def key_attribute(self):
        return 'id'

    async def get_all_items(self):
        return self._item_list


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.object_registry.register_actor(
            htypes.available_view_list.available_view_list,
            AvailableViewList.from_piece,
            services.mosaic,
            services.web,
            services.object_factory,
            services.view_factory_registry,
            services.available_view_registry,
            )
