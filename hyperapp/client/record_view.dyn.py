from functools import partial

from PySide2 import QtCore, QtWidgets

from hyperapp.client.commander import FreeFnCommand
from hyperapp.client.module import ClientModule

from . import htypes
from .layout import RootVisualItem, Layout
from .view_registry import NotApplicable
from .record_object import RecordObject


class RecordView(QtWidgets.QWidget):

    @classmethod
    async def make(cls, view_producer_registry, object, command_hub, piece_opener, fields=None):
        view = cls(object)
        await view._async_init(view_producer_registry, command_hub, piece_opener, fields)
        return view

    def __init__(self, object):
        super().__init__()
        self._object = object

    async def _async_init(self, view_producer_registry, command_hub, piece_opener, fields):
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
                view_producer_registry, qt_layout, field_id, field, command_hub, piece_opener, layout)
            if field_view.sizePolicy().verticalPolicy() & QtWidgets.QSizePolicy.ExpandFlag:
                has_expandable_field = True
            self._field_views.append(field_view)
        if not has_expandable_field:
            qt_layout.addStretch()
        self.setLayout(qt_layout)

    async def _construct_field_view(
            self, view_producer_registry, qt_layout, field_id, field, command_hub, piece_opener, layout):
        layout = await view_producer_registry.produce_layout(field.piece, field.object, command_hub, piece_opener)
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

    def __init__(self, view_producer_registry, params_editor, object, path, command_hub, piece_opener, fields=None):
        super().__init__(path)
        self._view_producer_registry = view_producer_registry
        self._params_editor = params_editor
        self._object = object
        self._command_hub = command_hub
        self._piece_opener = piece_opener
        self._fields = fields  # htypes.record_view.record_field list

    def get_view_ref(self):
        assert 0  # todo

    async def create_view(self):
        return (await RecordView.make(self._view_producer_registry, self._object, self._command_hub, self._piece_opener, self._fields))

    async def visual_item(self):
        return RootVisualItem('RecordView')  # todo: add fields children

    def get_current_commands(self):
        return list(self._get_object_commands())

    def _get_object_commands(self):
        for command in self._object.get_command_list():
            yield FreeFnCommand.from_command(command, partial(self._run_command, command))

    async def _run_command(self, command, *args, **kw):
        if command.more_params_are_required(*args, *kw):
            piece = await self._params_editor(self._piece, command, args, kw)
        else:
            piece = await command.run(*args, **kw)
        if piece is None:
            return
        await self._piece_opener(piece)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._view_producer_registry = services.view_producer_registry
        self._params_editor = services.params_editor
        services.view_producer_registry.register_view_producer(self._produce_view)

    async def _produce_view(self, piece, object, command_hub, piece_opener):
        if not isinstance(object, RecordObject):
            raise NotApplicable(object)
        return RecordViewLayout(self._view_producer_registry, self._params_editor, object, [], command_hub, piece_opener)
