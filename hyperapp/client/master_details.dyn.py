from abc import ABCMeta, abstractmethod
import asyncio
import logging

from PySide import QtCore, QtGui

from hyperapp.client.module import ClientModule
from . import htypes
from .composite import Composite
from .layout_registry import LayoutViewProducer

_log = logging.getLogger(__name__)


class MasterDetailsView(QtGui.QSplitter, Composite):

    def __init__(self, object_registry, view_producer, master, details_command, sizes=None):
        QtGui.QSplitter.__init__(self, QtCore.Qt.Vertical)
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
        QtGui.QSplitter.setVisible(self, visible)
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


class MasterDetailProducer(LayoutViewProducer):

    def __init__(self, layout, object_registry, view_producer):
        self._command_id = layout.command_id
        self._object_registry = object_registry
        self._view_producer = view_producer

    async def produce_view(self, piece, object, observer=None):
        details_command = object.get_command(self._command_id)
        master = await self._view_producer.produce_default_view(piece, object, observer)
        return MasterDetailsView(self._object_registry, self._view_producer, master, details_command)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.layout_registry.register_type(
            htypes.master_details.master_details_layout, MasterDetailProducer, services.object_registry, services.view_producer)
