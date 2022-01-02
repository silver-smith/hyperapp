from collections import namedtuple

from . import htypes
from .command import command
from .simple_list_object import SimpleListObject
from .module import ClientModule


Item = namedtuple('Item', 'idx dir dir_str persist values')


class LcsList(SimpleListObject):

    dir_list = [
        *SimpleListObject.dir_list,
        [htypes.lcs_list.lcs_list_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, mosaic, lcs, async_web):
        filter_dir = {
            await async_web.summon(ref)
            for ref in piece.filter_dir
            }
        return cls(mosaic, lcs, filter_dir)

    def __init__(self, mosaic, lcs, filter_dir):
        super().__init__()
        self._mosaic = mosaic
        self._lcs = lcs
        self._filter_dir = filter_dir
        self._items = None
        self._populate()

    def _populate(self):
        self._items = {
            idx: Item(
                idx=idx,
                dir=dir,
                dir_str='/'.join(str(element) for element in dir),
                persist=persist,
                values=', '.join(str(v) for v in value_list),
                )
            for idx, (dir, value_list, persist)
            in enumerate(self._lcs.iter(self._filter_dir))
            }

    @property
    def piece(self):
        return htypes.lcs_list.lcs_list(
            filter_dir=[
                self._mosaic.put(p)
                for p in self._filter_dir
                ],
            )

    @property
    def title(self):
        name = "Layered config sheet"
        if not self._filter_dir:
            return name
        filter = '&'.join(
            str(p) for p in self._filter_dir
            )
        return f"{name}: {filter}"

    @property
    def key_attribute(self):
        return 'idx'

    async def get_all_items(self):
        return list(self._items.values())

    def update(self):
        self._populate()
        super().update()

    @command
    async def remove_element(self, current_key):
        item = self._items[current_key]
        self._lcs.remove(item.dir)
        self.update()


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.object_registry.register_actor(
            htypes.lcs_list.lcs_list,
            LcsList.from_piece,
            services.mosaic,
            services.lcs,
            services.async_web,
            )

    @command
    async def open_lcs_list(self):
        return htypes.lcs_list.lcs_list([])
