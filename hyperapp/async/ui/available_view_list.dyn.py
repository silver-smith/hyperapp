import itertools
import logging
from collections import namedtuple

from hyperapp.common.htypes import tInt
from hyperapp.common.module import Module

from . import htypes
from .column import Column
from .simple_list_object import SimpleListObject

log = logging.getLogger(__name__)


Item = namedtuple('Item', 'id dir view view_str')


class AvailableViewList(SimpleListObject):

    dir_list = [
        *SimpleListObject.dir_list,
        [htypes.available_view_list.available_view_list_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, mosaic, lcs, object_factory):
        object = await object_factory.invite(piece.piece_ref)
        return cls(mosaic, lcs, object)

    def __init__(self, mosaic, lcs, object):
        super().__init__()
        self._mosaic = mosaic
        self._lcs = lcs
        self._object = object

    @property
    def piece(self):
        piece_ref = self._mosaic.put(self._object.piece)
        return htypes.available_view_list.available_view_list(piece_ref)

    @property
    def title(self):
        return f"Available views for: {self._object.title}"

    @property
    def columns(self):
        return [
            Column('id', type=tInt, is_key=True),
            Column('dir'),
            Column('view_str'),
            ]

    async def get_all_items(self):
        return list(self._iter_items())

    def _iter_items(self):
        id_it = itertools.count()
        for dir in self._object.dir_list:
            dir_str = '/'.join(str(element) for element in dir)
            none_available = True
            for piece in self._lcs.iter([[htypes.view.view_d('available'), *dir]]):
                yield Item(next(id_it), dir_str, piece, str(piece))
                none_available = False
            if none_available:
                yield Item(next(id_it), dir_str, None, '(no views available)')


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.object_registry.register_actor(
            htypes.available_view_list.available_view_list,
            AvailableViewList.from_piece,
            services.mosaic,
            services.lcs,
            services.object_factory,
            )
