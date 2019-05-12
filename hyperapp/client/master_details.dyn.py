from abc import ABCMeta, abstractmethod
import asyncio

from PySide import QtCore, QtGui

from hyperapp.common.capsule_registry import CapsuleRegistry, CapsuleResolver
from hyperapp.client.module import ClientModule
from . import htypes
from .composite import Composite


MODULE_NAME = 'master_details'


class DetailsConstructor(metaclass=ABCMeta):

    @abstractmethod
    def construct_details_handle(self, master_view, current_key):
        pass


class MasterDetailsView(QtGui.QSplitter, Composite):

    impl_id = 'master_details'

    @classmethod
    async def from_state(cls, locale, state, parent, details_constructor_resolver, view_registry):
        master = await view_registry.resolve_async(locale, state.master_handle)
        details_constructor = details_constructor_resolver.resolve(state.details_constructor_ref)
        return cls(locale, parent, view_registry, master, state.details_constructor_ref, details_constructor, state.sizes)

    def __init__(self, locale, parent, view_registry, master, details_constructor_ref, details_constructor, sizes):
        QtGui.QSplitter.__init__(self, QtCore.Qt.Vertical)
        Composite.__init__(self, parent, [master])
        self._locale = locale
        self._view_registry = view_registry
        self._master = master
        self._details_constructor_ref = details_constructor_ref
        self._details_constructor = details_constructor
        self._want_sizes = sizes
        master.set_parent(self)
        self.insertWidget(0, master.get_widget())
        asyncio.ensure_future(self._set_details(master.current_item_path))

    def get_state(self):
        return htypes.master_details.master_details_handle(
            view_id=self.impl_id,
            master_handle=self._master.get_state(),
            details_constructor_ref=self._details_constructor_ref,
            sizes=self.sizes(),
            )

    def get_current_child(self):
        return self._master

    async def _set_details(self, item_path):
        details_handle = self._details_constructor.construct_details_handle(self._master, item_path)
        if details_handle is None:
            return
        details = await self._view_registry.resolve_async(self._locale, details_handle)
        details.set_parent(self)
        self.insertWidget(1, details.get_widget())
        if self._want_sizes:
            self.setSizes(self._want_sizes)
            self._want_sizes = None


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.details_constructor_registry = dc_registry = CapsuleRegistry('details_constructor', services.type_resolver)
        services.details_constructor_resolver = dc_resolver = CapsuleResolver(services.ref_resolver, dc_registry)
        services.view_registry.register(MasterDetailsView.impl_id, MasterDetailsView.from_state, dc_resolver, services.view_registry)
