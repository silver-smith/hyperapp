from abc import ABCMeta, abstractmethod
import asyncio
import logging

from PySide2 import QtCore, QtWidgets

from . import htypes
from .command import command
from .composite import Composite
from .list_object import ListObject
from .tree_object import TreeObject
from .module import ClientModule

_log = logging.getLogger(__name__)


class MasterDetailsView(QtWidgets.QSplitter, Composite):

    @classmethod
    async def from_piece(cls, piece, object, add_dir_list, mosaic, object_factory, object_commands_factory, view_registry, view_producer):
        master_view = await view_registry.invite(piece.master_view_ref, object, [])
        return cls(mosaic, object_factory, object_commands_factory, view_producer, object, master_view, piece.open_command_id)

    def __init__(self, mosaic, object_factory, object_commands_factory, view_producer, master_object, master_view, details_command_id, sizes=None):
        QtWidgets.QSplitter.__init__(self, QtCore.Qt.Vertical)
        Composite.__init__(self, children=[master_view])
        self._mosaic = mosaic
        self._object_factory = object_factory
        self._object_commands_factory = object_commands_factory
        self._view_producer = view_producer
        self._master_object = master_object
        self._master_view = master_view
        self._details_command_id = details_command_id
        self._want_sizes = sizes
        self.insertWidget(0, master_view)
        master_view.add_observer(self)

    def setVisible(self, visible):
        QtWidgets.QSplitter.setVisible(self, visible)
        if visible:
            self.widget(0).setFocus()

    @property
    def piece(self):
        return htypes.master_details.master_details_view(
            master_view_ref=self._mosaic.put(self._master_view.piece),
            open_command_id=self._details_command_id,
            )

    @property
    def state(self):
        return self._master_view.state

    @property
    def object(self):
        return self._master_object

    def get_current_child(self):
        return self._master_view

    def current_changed(self, current_key):
        asyncio.ensure_future(self._update_details(current_key))

    async def _update_details(self, current_key):
        if self.count() > 1:
            w = self.widget(1)
            w.setParent(None)
            w.deleteLater()
        try:
            details_command = await self._object_commands_factory.command_by_name(self._master_object, self._details_command_id)
        except KeyError:
            _log.warning("Master %s does not has command %r", self._master_object, self._details_command_id)
            return
        master_state = self._master_view.state
        _log.info('Run command to open details: %r, state: %r', details_command.name, master_state)
        details_piece = await details_command.run(self._master_object, master_state, origin_dir=None)
        if details_piece is None:
            return
        details_object = await self._object_factory.animate(details_piece)
        details_view = await self._view_producer.create_view(details_object)
        self.insertWidget(1, details_view)
        if self._want_sizes:
            self.setSizes(self._want_sizes)
            self._want_sizes = None


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.view_registry.register_actor(
            htypes.master_details.master_details_view,
            MasterDetailsView.from_piece,
            services.mosaic,
            services.object_factory,
            services.object_commands_factory,
            services.view_registry,
            services.view_producer,
            )
        services.view_factory_registry.register_actor(
            htypes.master_details.master_details_view_factory,
            self._master_details_view_factory,
            services.mosaic,
            services.object_commands_factory,
            services.view_producer,
            )

        services.available_view_registry.add_factory(
            ListObject.dir_list[-1], htypes.master_details.master_details_view_factory())

    async def _master_details_view_factory(self, piece, object, mosaic, object_commands_factory, view_producer):
        for dir, view_piece in view_producer.iter_matched_pieces(object):
            if not isinstance(view_piece, htypes.master_details.master_details_view):
                break
        master_view_ref = mosaic.put(view_piece)
        name_to_command = {
            command.name: command
            for command
            in await object_commands_factory.get_object_command_list(object)
            }
        open_command = name_to_command.get('open')
        if open_command:
            command = open_command
        elif name_to_command:
            command = list(name_to_command.values())[0]
        else:
            return None
        return htypes.master_details.master_details_view(
            master_view_ref=master_view_ref,
            open_command_id=command.name,
            )
