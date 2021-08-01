from functools import partial

from PySide2 import QtCore, QtWidgets

from hyperapp.common.module import Module

from . import htypes
from .record_object import RecordObject, record_field_dir_list


class RecordView(QtWidgets.QWidget):

    @classmethod
    async def from_piece(cls, piece, object, view_factory):
        view = cls(object)
        await view._async_init(view_factory)
        return view

    def __init__(self, object):
        super().__init__()
        self.object = object

    async def _async_init(self, view_factory):
        layout = QtWidgets.QVBoxLayout()
        has_expandable_field = False
        self._field_view_dict = {}
        for field_id, field_object in self.object.fields.items():
            field_view = await self._construct_field_view(view_factory, layout, field_id, field_object)
            if field_view.sizePolicy().verticalPolicy() & QtWidgets.QSizePolicy.ExpandFlag:
                has_expandable_field = True
            self._field_view_dict[field_id] = field_view
        if not has_expandable_field:
            layout.addStretch()
        self.setLayout(layout)

    async def _construct_field_view(self, view_factory, layout, field_id, field_object):
        dir_list = record_field_dir_list(self.object.dir_list, field_id, field_object)
        view = await view_factory.create_view(field_object, dir_list)
        label = QtWidgets.QLabel(field_id)
        label.setBuddy(view)
        layout.addWidget(label)
        layout.addWidget(view)
        layout.addSpacing(10)
        return view

    @property
    def piece(self):
        return htypes.record_view.record_view()

    @property
    def state(self):
        return htypes.record_view.record_view_state()

    @property
    def title(self):
        return self.object.title

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
        return list(self.object.fields)[0]  # todo

    def get_field_view(self, field_id):
        return self._field_view_dict[field_id]


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.lcs.set([htypes.view.view_d('default'), *RecordObject.dir_list[-1]], htypes.record_view.record_view())
        services.view_registry.register_actor(htypes.record_view.record_view, RecordView.from_piece, services.view_factory)
