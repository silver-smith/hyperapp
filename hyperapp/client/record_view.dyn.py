from functools import partial

from PySide2 import QtCore, QtWidgets

from hyperapp.client.module import ClientModule

from . import htypes
from .layout import RootVisualItem, ObjectLayout
from .record_object import RecordObject


class RecordView(QtWidgets.QWidget):

    @classmethod
    async def make(cls, object_layout_producer, object, command_hub, fields=None):
        view = cls(object)
        await view._async_init(object_layout_producer, command_hub, fields)
        return view

    def __init__(self, object):
        super().__init__()
        self._object = object

    async def _async_init(self, object_layout_producer, command_hub, fields):
        # if fields:
        #     field_to_layout_ref = {field.field_id: field.layout_ref for field in fields}
        # else:
        #     field_to_layout_ref = {}
        qt_layout = QtWidgets.QVBoxLayout()
        has_expandable_field = False
        self._field_views = []
        for field_id, field_object in self._object.fields.items():
            # layout_ref = field_to_layout_ref.get(field_id)
            layout = None  # todo
            field_view = await self._construct_field_view(
                object_layout_producer, qt_layout, field_id, field_object, command_hub, layout)
            if field_view.sizePolicy().verticalPolicy() & QtWidgets.QSizePolicy.ExpandFlag:
                has_expandable_field = True
            self._field_views.append(field_view)
        if not has_expandable_field:
            qt_layout.addStretch()
        self.setLayout(qt_layout)

    async def _construct_field_view(
            self, object_layout_producer, qt_layout, field_id, field_object, command_hub, layout):
        layout = await object_layout_producer.produce_layout(field_object)
        view = await layout.create_view(command_hub)
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
            self._field_views[0].setFocus()


class RecordViewLayout(ObjectLayout):

    async def from_data(state, object, object_layout_producer, params_editor):
        return RecordViewLayout(object_layout_producer, params_editor, object, [])

    def __init__(self, object_layout_producer, params_editor, object, path, fields=None):
        super().__init__(path)
        self._object_layout_producer = object_layout_producer
        self._params_editor = params_editor
        self._object = object
        self._fields = fields  # htypes.record_view.record_field list; currently unused (todo).

    @property
    def data(self):
        return htypes.record_view.record_layout()

    async def create_view(self, command_hub):
        return (await RecordView.make(self._object_layout_producer, self._object, command_hub, self._fields))

    async def visual_item(self):
        return RootVisualItem('RecordView')  # todo: add fields children

    def get_current_commands(self, view):
        return list(self._get_object_commands())

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
