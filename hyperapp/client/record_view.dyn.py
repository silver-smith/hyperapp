from functools import partial

from PySide2 import QtCore, QtWidgets

from hyperapp.client.module import ClientModule

from . import htypes
from .layout import RootVisualItem, ObjectLayout
from .record_object import RecordObject


class RecordView(QtWidgets.QWidget):

    @classmethod
    async def make(cls, object_layout_producer, object, command_hub, field_layout_dict):
        view = cls(object)
        await view._async_init(object_layout_producer, command_hub, field_layout_dict)
        return view

    def __init__(self, object):
        super().__init__()
        self._object = object

    async def _async_init(self, object_layout_producer, command_hub, field_layout_dict):
        qt_layout = QtWidgets.QVBoxLayout()
        has_expandable_field = False
        self._field_view_dict = {}
        for field_id, field_layout in field_layout_dict.items():
            field_view = await self._construct_field_view(
                object_layout_producer, command_hub, qt_layout, field_id, field_layout)
            if field_view.sizePolicy().verticalPolicy() & QtWidgets.QSizePolicy.ExpandFlag:
                has_expandable_field = True
            self._field_view_dict[field_id] = field_view
        if not has_expandable_field:
            qt_layout.addStretch()
        self.setLayout(qt_layout)

    async def _construct_field_view(
            self, object_layout_producer, command_hub, qt_layout, field_id, field_layout):
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

    async def from_data(state, object, object_layout_producer, params_editor):
        self = RecordViewLayout(object_layout_producer, params_editor, object, [])
        await self._async_init(object_layout_producer)
        return self

    def __init__(self, object_layout_producer, params_editor, object, path, fields=None):
        super().__init__(path)
        self._object_layout_producer = object_layout_producer
        self._params_editor = params_editor
        self._object = object
        self._field_layout_dict = {}

    async def _async_init(self, object_layout_producer):
        for field_id, field_object in self._object.fields.items():
            layout = await object_layout_producer.produce_layout(field_object)
            self._field_layout_dict[field_id] = layout

    @property
    def data(self):
        return htypes.record_view.record_layout()

    async def create_view(self, command_hub):
        return (await RecordView.make(self._object_layout_producer, self._object, command_hub, self._field_layout_dict))

    async def visual_item(self):
        return RootVisualItem('RecordView')  # todo: add fields children

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
        services.default_object_layouts.register('record', RecordObject.category_list, self._make_record_layout_rec)
        services.available_object_layouts.register('record', RecordObject.category_list, self._make_record_layout_rec)
        services.object_layout_registry.register_type(
            htypes.record_view.record_layout, RecordViewLayout.from_data, services.object_layout_producer, services.params_editor)

    async def _make_record_layout_rec(self, object):
        return htypes.record_view.record_layout()
