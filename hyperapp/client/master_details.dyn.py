from abc import ABCMeta, abstractmethod
import asyncio
import logging

from PySide2 import QtCore, QtWidgets

from hyperapp.client.module import ClientModule

from . import htypes
from .composite import Composite
from .layout import RootVisualItem, Layout
from .list_object import ListObject

_log = logging.getLogger(__name__)


class MasterDetailsView(QtWidgets.QSplitter, Composite):

    def __init__(self, object_registry, view_producer, master, details_command, sizes=None):
        QtWidgets.QSplitter.__init__(self, QtCore.Qt.Vertical)
        Composite.__init__(self, children=[master])
        self._object_registry = object_registry
        self._view_producer = view_producer
        self._master = master
        self._details_command = details_command
        self._want_sizes = sizes
        master.set_parent(self)
        self.insertWidget(0, master)
        master.add_observer(self)

    def setVisible(self, visible):
        QtWidgets.QSplitter.setVisible(self, visible)
        if visible:
            self.widget(0).setFocus()

    def get_current_child(self):
        return self._master

    def current_changed(self, current_key):
        asyncio.ensure_future(self._update_details(current_key))

    async def _update_details(self, current_key):
        if self.count() > 1:
            w = self.widget(1)
            w.setParent(None)
            w.deleteLater()
        _log.info('Run command to open details: %r', self._details_command.id)
        piece = await self._details_command.run(current_key)
        if not piece:
            return
        object = await self._object_registry.resolve_async(piece)
        view = await self._view_producer.produce_view(piece, object)
        self.insertWidget(1, view)
        if self._want_sizes:
            self.setSizes(self._want_sizes)
            self._want_sizes = None


class MasterDetailsLayout(Layout):

    def __init__(self, piece, object, path, command_hub, piece_opener):
        super().__init__(path)
        self._command_hub = command_hub
        self._piece_opener = piece_opener
        self._piece = piece
        self._object = object

    def get_view_ref(self):
        assert 0  # todo

    async def create_view(self):
        assert 0  # todo

    async def visual_item(self):
        return RootVisualItem('MasterDetails')


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._view_producer_registry = services.view_producer_registry
        services.object_layout_registry.register_type(
            htypes.master_details.master_details_layout, self._produce_master_detail_layout)
        services.object_layout_list.append(
            services.ref_registry.register_object(
                htypes.master_details.master_details_layout(command_id='details')))

    async def _produce_master_detail_layout(self, piece, object, command_hub, piece_opener):
        if not isinstance(object, ListObject):
            raise NotApplicable(object)
        return MasterDetailsLayout(piece, object, [], command_hub, piece_opener)

        # layout = await self._view_producer_registry.produce_layout(piece, object, [], command_hub, piece_opener)
        # details_command = object.get_command(piece.command_id)
        # master = await self._view_producer.produce_default_view(piece, object, observer)
        # return MasterDetailsView(self._object_registry, self._view_producer, master, details_command)
