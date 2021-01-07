from functools import partial

from PySide2 import QtCore, QtWidgets

from hyperapp.client.module import ClientModule

from . import htypes
from .layout import ObjectLayout
from .record_object import RecordObject


class RecordView(QtWidgets.QWidget):

    @classmethod
    async def make(cls, command_hub, object, field_layout_dict):
        view = cls(object)
        await view._async_init(command_hub, field_layout_dict)
        return view

    def __init__(self, object):
        super().__init__()
        self._object = object

    async def _async_init(self, command_hub, field_layout_dict):
        qt_layout = QtWidgets.QVBoxLayout()
        has_expandable_field = False
        self._field_view_dict = {}
        for field_id, field_layout in field_layout_dict.items():
            field_view = await self._construct_field_view(
                command_hub, qt_layout, field_id, field_layout)
            if field_view.sizePolicy().verticalPolicy() & QtWidgets.QSizePolicy.ExpandFlag:
                has_expandable_field = True
            self._field_view_dict[field_id] = field_view
        if not has_expandable_field:
            qt_layout.addStretch()
        self.setLayout(qt_layout)

    async def _construct_field_view(
            self, command_hub, qt_layout, field_id, field_layout):
        field_object = self._object.fields[field_id]
        view = await field_layout.create_view(command_hub, field_object)
        label = QtWidgets.QLabel(field_id)
        label.setBuddy(view)
        qt_layout.addWidget(label)
        qt_layout.addWidget(view)
        qt_layout.addSpacing(10)
        return view

    @property
    def title(self):
        return self._object.title

    def get_widget(self):
        return self

    def ensure_has_focus(self):
        self.setFocus()

    def setVisible(self, visible):
        super().setVisible(visible)
        if visible:
            first_view = list(self._field_view_dict.values())[0]
            first_view.setFocus()

    @property
    def focused_field_id(self):
        return list(self._object.fields)[0]  # todo

    def get_field_view(self, field_id):
        return self._field_view_dict[field_id]


class RecordViewLayout(ObjectLayout):

    async def from_data(state, path, layout_watcher, mosaic, async_ref_resolver, object_layout_registry):
        object_type = await async_ref_resolver.summon(state.object_type_ref)
        self = RecordViewLayout(mosaic, path, object_type, state.command_list)
        await self._async_init(layout_watcher, async_ref_resolver, object_layout_registry, state.field_layout_list)
        return self

    def __init__(self, mosaic, path, object_type, command_list_data):
        super().__init__(mosaic, path, object_type, command_list_data)
        self._field_layout_dict = {}

    async def _async_init(self, layout_watcher, async_ref_resolver, object_layout_registry, field_layout_list):
        field_id_to_type_ref = {
            field.id: field.object_type_ref
            for field in self._object_type.field_type_list
            }
        for idx, field in enumerate(field_layout_list):
            field_object_type_ref = field_id_to_type_ref[field.id]
            field_object_type = await async_ref_resolver.summon(field_object_type_ref)
            path = [*self._path, idx]
            layout = await object_layout_registry.invite(field.layout_ref, path, layout_watcher)
            self._field_layout_dict[field.id] = layout

    @property
    def data(self):
        field_layout_list = []
        for field_id, layout in self._field_layout_dict.items():
            layout_ref = self._mosaic.put(layout.data)
            field_layout_list.append(htypes.record_view.record_layout_field(field_id, layout_ref))
        return htypes.record_view.record_layout(self._object_type_ref, self._command_list_data, field_layout_list)

    async def create_view(self, command_hub, object):
        return (await RecordView.make(command_hub, object, self._field_layout_dict))

    async def visual_item(self):
        children = [
            await layout.visual_item()
            for layout in self._field_layout_dict.values()
            ]
        return self.make_visual_item('RecordView', children=children)

    def get_current_commands(self, object, view):
        field_id = view.focused_field_id
        focused_object = object.fields[field_id]
        focused_layout = self._field_layout_dict[field_id]
        focused_view = view.get_field_view(field_id)
        return [
            *super().get_current_commands(object, view),
            *focused_layout.get_current_commands(focused_object, focused_view),
            ]


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        self._mosaic = services.mosaic
        self._async_ref_resolver = services.async_ref_resolver
        self._layout_handle_from_object_type = services.layout_handle_from_object_type
        services.available_object_layouts.register('record', [RecordObject.type._t], self._make_record_layout_data)
        services.default_object_layouts.register('record', [RecordObject.type._t], self._make_record_layout_data)
        services.object_layout_registry.register_actor(
            htypes.record_view.record_layout, RecordViewLayout.from_data,
            services.mosaic, services.async_ref_resolver, services.object_layout_registry)

    async def _make_record_layout_data(self, object_type):
        object_type_ref = self._mosaic.put(object_type)
        command_list = ObjectLayout.make_default_command_list(object_type)
        field_layout_list = []
        for field in object_type.field_type_list:
            field_object_type = await self._async_ref_resolver.summon(field.object_type_ref)
            layout_handle = await self._layout_handle_from_object_type(field_object_type)
            layout_ref = self._mosaic.put(layout_handle.layout.data)
            field_layout_list.append(htypes.record_view.record_layout_field(field.id, layout_ref))
        return htypes.record_view.record_layout(object_type_ref, command_list, field_layout_list)
