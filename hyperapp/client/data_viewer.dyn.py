from collections import namedtuple

from hyperapp.common.ref import ref_repr
from hyperapp.common.visual_rep import VisualRepEncoder
from hyperapp.client.module import ClientModule
from . import htypes
from .items_object import Column
from .tree_object import TreeObject


MODULE_NAME = 'data_viewer'


ValueItem = namedtuple('ValueItem', 'idx t name value')


def _load_visual_rep(t, value):
    path2item_list = {}

    def add_rep(path, idx, rep):
        item = ValueItem(idx, rep.t, rep.name, rep.value)
        path2item_list.setdefault(path, []).append(item)
        for i, child in enumerate(rep.children):
            add_rep(path + (idx,), i, child)

    rep = VisualRepEncoder().encode(t, value)
    add_rep((), 0, rep)
    return path2item_list


class DataViewer(TreeObject):

    @classmethod
    def from_state(cls, state, type_resolver):
        dc = type_resolver.resolve_ref(state.data_ref)
        return cls(state.data_ref, dc.t, dc.value)

    def __init__(self, data_ref, t, value):
        super().__init__()
        self._data_ref = data_ref
        self._t = t
        self._path2item_list = _load_visual_rep(t, value)

    def get_title(self):
        return "{} ({})".format(ref_repr(self._data_ref), self._t.name)

    def get_columns(self):
        return [
            Column('name'),
            Column('t'),
            Column('value'),
            ]

    @property
    def key_attribute(self):
        return 'idx'

    async def fetch_items(self, path):
        path = tuple(path)
        item_list = self._path2item_list.get(path, [])
        for item in item_list:
            p = path + (item.idx,)
            if p not in self._path2item_list:
                self._distribute_fetch_results(p, [])
        self._distribute_fetch_results(path, item_list)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.object_registry.register_type(htypes.data_viewer.data_viewer, DataViewer.from_state, services.type_resolver)
