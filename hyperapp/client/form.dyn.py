import logging
from enum import Enum
from collections import OrderedDict
from PySide import QtCore, QtGui

from hyperapp.client.util import call_after
from hyperapp.client.object import Object
from hyperapp.client.mode_command import BoundModeCommand
from hyperapp.client.module import ClientModule
from . import htypes
from .objimpl_registry import ObjImplRegistry
from .composite import Composite

log = logging.getLogger(__name__)


class FormObject(Object):

    impl_id = 'form'

    @classmethod
    def from_state(cls, state, field_object_map):
        return cls(field_object_map)

    def __init__(self, field_object_map):
        super().__init__()
        self._fields = field_object_map

    def get_title(self):
        return 'form'

    def get_state(self):
        return htypes.form.form_object(self.impl_id)


class FormView(Composite, QtGui.QWidget):

    impl_id = 'form'

    class Mode(Enum):
        VIEW = 'view'
        EDIT = 'edit'

    @classmethod
    async def from_state(cls, locale, state, parent, form_impl_registry, view_registry):
        field_view_map = OrderedDict()
        field_object_map = {}
        for field in state.field_list:
            field_view_map[field.id] = view = await view_registry.resolve_async(locale, field.view)
            field_object_map[field.id] = view.get_object()
        object = await form_impl_registry.resolve_async(state.object, field_object_map)
        return cls(parent, object, field_view_map, cls.Mode(state.mode), state.current_field_id)

    def __init__(self, parent, object, field_view_map, mode, current_field_id):
        QtGui.QWidget.__init__(self)
        Composite.__init__(self, parent, list(field_view_map.values()))
        self._object = object
        self._field_view_map = field_view_map
        self._mode = mode
        layout = QtGui.QVBoxLayout()
        for id, field_view in field_view_map.items():
            self._construct_field(layout, id, field_view, focus_it = id==current_field_id)
        if not any(view.sizePolicy().verticalPolicy() & QtGui.QSizePolicy.ExpandFlag for view in field_view_map.values()):
            layout.addStretch()
        self.setLayout(layout)

    def get_state(self):
        current_field_id = list(self._field_view_map.keys())[0]
        field_list = []
        for id, field_view in self._field_view_map.items():
            field_list.append(htypes.form.form_view_field(id, field_view.get_state()))
            if field_view.has_focus():
                current_field_id = id
        return htypes.form.form_handle(self.impl_id, self._object.get_state(), field_list, self._mode.value, current_field_id)

    def get_object(self):
        return self._object

    def get_widget_to_focus(self):
        return list(self._field_view_map.values())[0]

    def get_object_command_list(self, object, kinds=None):
        command_list = Composite.get_object_command_list(self, object, kinds)
        return list(filter(self._mode_command_pred, command_list))

    def _mode_command_pred(self, command):
        if isinstance(command, BoundModeCommand):
            return command.mode == self._mode
        else:
            return True

    def _construct_field(self, layout, id, field_view, focus_it):
        label = QtGui.QLabel(id)
        label.setBuddy(field_view)
        layout.addWidget(label)
        layout.addWidget(field_view)
        layout.addSpacing(10)
        field_view.set_parent(self)
        if focus_it:
            call_after(field_view.ensure_has_focus)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.form_impl_registry = form_impl_registry = ObjImplRegistry('form')
        form_impl_registry.register(FormObject.impl_id, FormObject.from_state)
        services.view_registry.register(FormView.impl_id, FormView.from_state, services.form_impl_registry, services.view_registry)
