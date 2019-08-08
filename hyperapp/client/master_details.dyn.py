from abc import ABCMeta, abstractmethod
import asyncio
import logging

from PySide import QtCore, QtGui

from hyperapp.client.module import ClientModule
from . import htypes
from .composite import Composite

_log = logging.getLogger(__name__)

MODULE_NAME = 'master_details'


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
        asyncio.ensure_future(self._set_details(current_key))

    async def _set_details(self, current_key):
        if self.count() > 1:
            w = self.widget(1)
            w.setParent(None)
            w.deleteLater()
        _log.info('Run command to open details: %r', self._details_command.id)
        state = await self._details_command.run(current_key)
        if not state:
            return
        object = await self._object_registry.resolve_async(state)
        view = self._view_producer.produce_view(state, object)
        self.insertWidget(1, view)
        if self._want_sizes:
            self.setSizes(self._want_sizes)
            self._want_sizes = None


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
