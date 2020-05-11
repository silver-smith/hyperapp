from abc import ABCMeta, abstractmethod
import asyncio
import logging

from PySide2 import QtCore, QtWidgets

from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .composite import Composite
from .layout import RootVisualItem, VisualItem, Layout
from .list_object import ListObject
from .tree_object import TreeObject
from .view_chooser import ViewFieldRef

_log = logging.getLogger(__name__)


class MasterDetailsView(QtWidgets.QSplitter, Composite):

    def __init__(self, object_registry, view_producer_registry, command_hub, piece_opener, master_view, details_command_id, sizes=None):
        QtWidgets.QSplitter.__init__(self, QtCore.Qt.Vertical)
        Composite.__init__(self, children=[master_view])
        self._object_registry = object_registry
        self._view_producer_registry = view_producer_registry
        self._command_hub = command_hub
        self._piece_opener = piece_opener
        self._master_view = master_view
        self._details_command_id = details_command_id
        self._want_sizes = sizes
        master_view.set_parent(self)
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
        master_object = self._master_view.get_object()
        try:
            details_command = master_object.get_command(self._details_command_id)
        except KeyError:
            _log.warning("Master %s does not has command %r", master_object, self._details_command_id)
            return
        _log.info('Run command to open details: %r', details_command.id)
        piece = await details_command.run(current_key)
        if not piece:
            return
        object = await self._object_registry.resolve_async(piece)
        layout = await self._view_producer_registry.produce_layout(piece, object, self._command_hub, self._piece_opener)
        view = await layout.create_view()
        self.insertWidget(1, view)
        if self._want_sizes:
            self.setSizes(self._want_sizes)
            self._want_sizes = None


class MasterDetailsLayout(Layout):

    def __init__(self, ref_registry, object_registry, view_producer_registry, object_layout_overrides,
                 command_id, piece, object, path, command_hub, piece_opener):
        super().__init__(path)
        self._ref_registry = ref_registry
        self._object_registry = object_registry
        self._view_producer_registry = view_producer_registry
        self._object_layout_overrides = object_layout_overrides
        self._details_command_id = command_id
        self._command_id = command_id
        self._command_hub = command_hub
        self._piece_opener = piece_opener
        self._piece = piece
        self._object = object

    def get_view_ref(self):
        # master_layout = await self._create_master_layout()
        master_layout_ref = master_layout.get_view_ref()
        layout_rec = htypes.master_details.master_details_layout(
            master_layout_ref=master_layout_ref,
            command_id=self._details_command_id,
            )
        return self._ref_registry.register_object(layout_rec)

    async def create_view(self):
        master_layout = await self._create_master_layout()
        master_view = await master_layout.create_view()
        return MasterDetailsView(
            self._object_registry, self._view_producer_registry,
            self._command_hub, self._piece_opener, master_view, self._details_command_id)

    async def visual_item(self):
        master_layout = await self._create_master_layout()
        master_item = await master_layout.visual_item()
        return RootVisualItem('MasterDetails', children=[
            master_item.to_item(0, 'master', commands=[self._replace_view]),
            VisualItem(1, 'command', str(self._details_command_id)),
            ])

    async def _create_master_layout(self):
        return (await self._view_producer_registry.produce_default_layout(
            self._piece, self._object, self._command_hub, self._piece_opener))

    @command('replace')
    async def _replace_view(self, path, view: ViewFieldRef):
        resource_key = self._object.hashable_resource_key
        self._object_layout_overrides[resource_key] = self.get_view_ref()
        piece_ref = self._ref_registry.register_object(self._piece)
        return htypes.layout_editor.object_layout_editor(piece_ref)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._ref_registry = services.ref_registry
        self._object_registry = services.object_registry
        self._view_producer_registry = services.view_producer_registry
        self._object_layout_overrides = services.object_layout_overrides
        services.object_layout_registry.register_type(
            htypes.master_details.master_details_layout, self._produce_master_detail_layout)
        services.object_layout_list.append(
            services.ref_registry.register_object(
                htypes.master_details.master_details_layout(master_layout_ref=None, command_id='open')))

    async def _produce_master_detail_layout(self, state, piece, object, command_hub, piece_opener):
        if not isinstance(object, (ListObject, TreeObject)):
            raise NotApplicable(object)
        return MasterDetailsLayout(
            self._ref_registry, self._object_registry, self._view_producer_registry, self._object_layout_overrides,
            state.command_id, piece, object, [], command_hub, piece_opener)
