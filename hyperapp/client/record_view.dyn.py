from functools import partial

from PySide2 import QtCore, QtWidgets

from hyperapp.client.module import ClientModule

from . import htypes
from .layout import ObjectLayout
from .record_object import RecordObject


class RecordView(QtWidgets.QWidget):

    @classmethod
    async def make(cls, object, command_hub, field_layout_dict):
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
        view = await field_layout.create_view(command_hub)
        label = QtWidgets.QLabel(field_id)
        label.setBuddy(view)
        qt_layout.addWidget(label)
        qt_layout.addWidget(view)
        qt_layout.addSpacing(10)
        return view

    def get_title(self):
        return self._object.get_title()

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

    async def from_data(state, path, object, layout_watcher, object_layout_resolver):
        self = RecordViewLayout(object, path, state.field_layout_list)
        await self._async_init(layout_watcher, object_layout_resolver)
        return self

    def __init__(self, object, path, field_layout_list):
        super().__init__(path)
        self._object = object
        self._field_layout_list = field_layout_list
        self._field_layout_dict = {}

    async def _async_init(self, layout_watcher, object_layout_resolver):
        for idx, field in enumerate(self._field_layout_list):
            path = [*self._path, idx]
            field_object = self._object.fields[field.id]
            layout = await object_layout_resolver.resolve(field.layout_ref, path, field_object, layout_watcher)
            self._field_layout_dict[field.id] = layout

    @property
    def data(self):
        return htypes.record_view.record_layout(self._field_layout_list)

    async def create_view(self, command_hub):
        return (await RecordView.make(self._object, command_hub, self._field_layout_dict))

    async def visual_item(self):
        children = [
            await layout.visual_item()
            for layout in self._field_layout_dict.values()
            ]
        return self.make_visual_item('RecordView', children=children)

    def get_current_commands(self, view):
        focused_layout = self._field_layout_dict[view.focused_field_id]
        focused_view = view.get_field_view(view.focused_field_id)
        return [
            *self._get_object_commands(),
            *focused_layout.get_current_commands(focused_view),
            ]

    def _get_object_commands(self):
        return self._object.get_all_command_list()


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._ref_registry = services.ref_registry
        self._object_layout_producer = services.object_layout_producer
        services.default_object_layouts.register('record', RecordObject.category_list, self._make_record_layout_rec)
        services.available_object_layouts.register('record', RecordObject.category_list, self._make_record_layout_rec)
        services.object_layout_registry.register_type(
            htypes.record_view.record_layout, RecordViewLayout.from_data, services.object_layout_resolver)

    async def _make_record_layout_rec(self, object):
        field_layout_list = []
        for field_id, field_object in object.fields.items():
            layout = await self._object_layout_producer.produce_layout(field_object, layout_watcher=None)
            layout_ref = self._ref_registry.register_object(layout.data)
            field_layout_list.append(htypes.record_view.record_layout_field(field_id, layout_ref))
        return htypes.record_view.record_layout(field_layout_list)
