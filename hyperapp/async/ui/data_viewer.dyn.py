from collections import defaultdict, namedtuple

from hyperapp.common.htypes import tInt, ref_t
from hyperapp.common.visual_rep import VisualRepEncoder
from hyperapp.common.module import Module

from . import htypes
from .command import command
from .column import Column
from .tree_object import TreeObject


ValueItem = namedtuple('ValueItem', 'idx t value name text')


class DataViewer(TreeObject):

    dir_list = [
        *TreeObject.dir_list,
        [htypes.data_viewer.data_viewer_d()],
        ]

    @classmethod
    async def from_piece(cls, state, mosaic, async_web):
        dc = mosaic.resolve_ref(state.data_ref)
        self = cls(state.data_ref, dc.t)
        await self._async_init(async_web, dc.t, dc.value)
        return self

    def __init__(self, data_ref, t):
        super().__init__()
        self._data_ref = data_ref
        self._t = t
        self._path2item_list = None

    async def _async_init(self, async_web, t, value):
        self._path2item_list = defaultdict(list)

        async def add_rep(path, idx, rep):
            if isinstance(rep.value, ref_t):
                target = await async_web.summon(rep.value)
                text = f"{rep.text}: {target}"
            else:
                text = rep.text
            item = ValueItem(idx, rep.t, rep.value, rep.name, text)
            self._path2item_list[path].append(item)
            for i, child in enumerate(rep.children):
                await add_rep(path + (idx,), i, child)

        rep = VisualRepEncoder().encode(t, value)
        await add_rep((), 0, rep)

    @property
    def piece(self):
        return htypes.data_viewer.data_viewer(self._data_ref)

    @property
    def title(self):
        return f"{self._data_ref} ({self._t.name})"

    @property
    def columns(self):
        return [
            Column('name'),
            Column('t'),
            Column('text'),
            ]

    @property
    def key_attribute(self):
        return 'idx'

    @property
    def key_t(self):
        return tInt

    async def fetch_items(self, path):
        path = tuple(path)
        item_list = self._path2item_list.get(path, [])
        for item in item_list:
            p = path + (item.idx,)
            if p not in self._path2item_list:
                self._distribute_fetch_results(p, [])
        self._distribute_fetch_results(path, item_list)

    @command
    async def open_ref(self, current_key):
        item_list = self._path2item_list[tuple(current_key[:-1])]
        item = item_list[current_key[-1]]
        if not isinstance(item.value, ref_t):
            return None
        return htypes.data_viewer.data_viewer(item.value)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.object_registry.register_actor(
            htypes.data_viewer.data_viewer,
            DataViewer.from_piece,
            services.mosaic,
            services.async_web,
            )
