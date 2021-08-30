from collections import namedtuple

from hyperapp.common.module import Module

from . import htypes
from .column import Column
from .simple_list_object import SimpleListObject


Item = namedtuple('Item', 'dir dir_str')


class DirList(SimpleListObject):

    dir_list = [
        *SimpleListObject.dir_list,
        [htypes.dir_list.dir_list_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, mosaic, async_web):
        async def dir_pieces(dir_refs):
            return [
                await async_web.summon(ref)
                for ref in dir_refs
                ]
        dir_list = [
            await dir_pieces(dir_refs)
            for dir_refs in piece.dir_ref_list
            ]
        return cls(mosaic, dir_list)

    def __init__(self, mosaic, dir_list):
        super().__init__()
        self._mosaic = mosaic
        self._dir_list = dir_list

    @property
    def piece(self):
        def dir_refs(dir):
            return [
                self._mosaic.put(piece)
                for piece in dir
            ]
        return htypes.dir_list.dir_list([
            dir_refs(dir)
            for dir in self._dir_list
            ])

    @property
    def title(self):
        return f"Dir list"

    @property
    def columns(self):
        return [
            Column('dir_str', is_key=True),
            ]

    async def get_all_items(self):
        return [
            Item(dir=dir, dir_str='/'.join(str(element) for element in dir))
            for dir in self._dir_list
            ]


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.object_registry.register_actor(
            htypes.dir_list.dir_list,
            DirList.from_piece,
            services.mosaic,
            services.async_web,
            )
