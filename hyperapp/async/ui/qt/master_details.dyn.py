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

    def __init__(self, object_registry, object_layout_producer, command_hub, master_view, details_command_id, sizes=None):
        QtWidgets.QSplitter.__init__(self, QtCore.Qt.Vertical)
        Composite.__init__(self, children=[master_view])
        self._object_registry = object_registry
        self._object_layout_producer = object_layout_producer
        self._command_hub = command_hub
        self._master_view = master_view
        self._details_command_id = details_command_id
        self._want_sizes = sizes
        self.insertWidget(0, master_view)
        master_view.add_observer(self)

    def setVisible(self, visible):
        QtWidgets.QSplitter.setVisible(self, visible)
        if visible:
            self.widget(0).setFocus()

    def get_current_child(self):
        return self._master_view

    def current_changed(self, current_key):
        asyncio.ensure_future(self._update_details(current_key))

    async def _update_details(self, current_key):
        if self.count() > 1:
            w = self.widget(1)
            w.setParent(None)
            w.deleteLater()
        master_object = self._master_view.object
        try:
            details_command = master_object.get_command(self._details_command_id)
        except KeyError:
            _log.warning("Master %s does not has command %r", master_object, self._details_command_id)
            return
        _log.info('Run command to open details: %r', details_command.id)
        resolved_piece = await details_command.run(current_key)
        if not resolved_piece:
            return
        view = await resolved_piece.layout.create_view(self._command_hub)
        self.insertWidget(1, view)
        if self._want_sizes:
            self.setSizes(self._want_sizes)
            self._want_sizes = None


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.view_registry.register_actor(
            htypes.master_details.master_details_view, self._open_master_details_view, services.mosaic, services.view_factory)
        services.lcs.add(
            [htypes.view.view_d('available'), *ListObject.dir_list[-1]],
            htypes.master_details.master_details_view(open_command_id='open'),
            )

        # self._default_object_layouts = services.default_object_layouts
        # object_type_ids = [*ListObject.type.ids, *TreeObject.type.ids]
        # services.available_object_layouts.register('master_details', object_type_ids, self._make_master_detail_layout_rec)
        # services.object_layout_registry.register_actor(
        #     htypes.master_details.master_details_layout,
        #     MasterDetailsLayout.from_data,
        #     services.mosaic,
        #     services.object_registry,
        #     services.object_layout_registry,
        #     services.object_layout_producer,
        #     )

    async def _open_master_details_view(self, piece, object, add_dir_list, mosaic, view_factory):
        assert 0, 'todo'

        # rec_it = self._default_object_layouts.resolve(object.category_list)
        # try:
        #     rec = next(rec_it)
        # except StopIteration:
        #     raise RuntimeError(f"At least one default category is expected for {object} categoriees: {object.category_list}.")
        # master_layout_rec = await rec.layout_rec_maker(object)
        # master_layout_ref = self._mosaic.put(master_layout_rec)
        # return htypes.master_details.master_details_layout(
        #     master_layout_ref=master_layout_ref,
        #     command_id='open',
        #     )
