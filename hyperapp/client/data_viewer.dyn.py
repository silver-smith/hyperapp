from hyperapp.common.htypes import tInt
from hyperapp.common.ref import ref_repr
from hyperapp.client.module import ClientModule
from . import htypes
from .items_object import Column
from .tree_object import TreeObject


MODULE_NAME = 'data_viewer'


class DataViewer(TreeObject):

    impl_id = 'data_viewer'

    @classmethod
    def from_state(cls, state, type_resolver):
        dc = type_resolver.resolve_ref(state.data_ref)
        return cls(state.data_ref, dc.t, dc.value)

    def __init__(self, data_ref, t, value):
        super().__init__()
        self._data_ref = data_ref
        self._t = t
        self._value = value

    def get_state(self):
        return htypes.data_viewer.data_viewer(self.impl_id, self._data_ref)

    def get_title(self):
        return "{} ({})".format(ref_repr(self._data_ref), self._t.name)

    def get_columns(self):
        return [
            Column('idx', type=tInt),
            Column('name'),
            Column('type'),
            Column('value'),
            ]

    async def fetch_items(self, path):
        path = tuple(path)
        self._distribute_fetch_results(path, [])


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.objimpl_registry.register(DataViewer.impl_id, DataViewer.from_state, services.type_resolver)
