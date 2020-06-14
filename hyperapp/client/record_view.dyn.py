from functools import partial

from PySide2 import QtCore, QtWidgets

from hyperapp.client.module import ClientModule

from . import htypes
from .layout import RootVisualItem, Layout
from .record_object import RecordObject


class RecordView(QtWidgets.QWidget):

    @classmethod
    async def make(cls, object_layout_producer, object, command_hub, piece_opener, fields=None):
        view = cls(object)
        await view._async_init(object_layout_producer, command_hub, piece_opener, fields)
        return view

    def __init__(self, object):
        super().__init__()
        self._object = object

    async def _async_init(self, object_layout_producer, command_hub, piece_opener, fields):
        # if fields:
        #     field_to_layout_ref = {field.field_id: field.layout_ref for field in fields}
        # else:
        #     field_to_layout_ref = {}
        qt_layout = QtWidgets.QVBoxLayout()
        has_expandable_field = False
        self._field_views = []
        for field_id, field in self._object.get_fields().items():
            # layout_ref = field_to_layout_ref.get(field_id)
            layout = None  # todo
            field_view = await self._construct_field_view(
                object_layout_producer, qt_layout, field_id, field, command_hub, piece_opener, layout)
            if field_view.sizePolicy().verticalPolicy() & QtWidgets.QSizePolicy.ExpandFlag:
                has_expandable_field = True
            self._field_views.append(field_view)
        if not has_expandable_field:
            qt_layout.addStretch()
        self.setLayout(qt_layout)

    async def _construct_field_view(
            self, object_layout_producer, qt_layout, field_id, field, command_hub, piece_opener, layout):
        layout = await object_layout_producer.produce_layout(field.object, command_hub, piece_opener)
        view = await layout.create_view()
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


class RecordViewLayout(Layout):

    def __init__(self, object_layout_producer, params_editor, object, path, command_hub, piece_opener, fields=None):
        super().__init__(path)
        self._object_layout_producer = object_layout_producer
        self._params_editor = params_editor
        self._object = object
        self._command_hub = command_hub
        self._piece_opener = piece_opener
        self._fields = fields  # htypes.record_view.record_field list

    def get_view_ref(self):
        assert 0  # todo

    async def create_view(self):
        return (await RecordView.make(self._object_layout_producer, self._object, self._command_hub, self._piece_opener, self._fields))

    async def visual_item(self):
        return RootVisualItem('RecordView')  # todo: add fields children

    def get_current_commands(self):
        return list(self._get_object_commands())

    def _get_object_commands(self):
        for command in self._object.get_command_list():
            yield (command
                   .with_(wrapper=self._piece_opener)
                   .with_(piece=self._object.data, params_editor=self._params_editor)
                   )


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._object_layout_producer = services.object_layout_producer
        self._params_editor = services.params_editor
        services.default_object_layouts.register('record', RecordObject.category_list, self._make_record_layout_rec)
        services.available_object_layouts.register('record', RecordObject.category_list, self._make_record_layout_rec)
        services.object_layout_registry.register_type(htypes.record_view.record_layout, self._produce_layout)

    async def _make_record_layout_rec(self, object):
        return htypes.record_view.record_layout()

    async def _produce_layout(self, state, object, command_hub, piece_opener):
        return RecordViewLayout(self._object_layout_producer, self._params_editor, object, [], command_hub, piece_opener)
