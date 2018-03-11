import logging
from enum import Enum
from collections import OrderedDict
from PySide import QtCore, QtGui

from ..common.interface import form as form_types
from .util import call_after
from .module import Module
from .objimpl_registry import ObjImplRegistry
from .object import Object
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
        return form_types.form_object(self.impl_id)


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
            field_view_map[field.id] = view = await view_registry.resolve(locale, field.view)
            field_object_map[field.id] = view.get_object()
        object = await form_impl_registry.resolve(state.object, field_object_map)
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
            field_list.append(form_types.form_view_field(id, field_view.get_state()))
            if field_view.has_focus():
                current_field_id = id
        return form_types.form_handle(self.impl_id, self._object.get_state(), field_list, current_field_id)

    def get_object(self):
        return self._object

    def get_widget_to_focus(self):
        return list(self._field_view_map.values())[0]

    def _construct_field(self, layout, id, field_view, focus_it):
        label = QtGui.QLabel(id)
        label.setBuddy(field_view)
        layout.addWidget(label)
        layout.addWidget(field_view)
        layout.addSpacing(10)
        field_view.set_parent(self)
        if focus_it:
            call_after(field_view.ensure_has_focus)


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(services)
        services.form_impl_registry = form_impl_registry = ObjImplRegistry('form')
        form_impl_registry.register(FormObject.impl_id, FormObject.from_state)
        services.view_registry.register(FormView.impl_id, FormView.from_state, services.form_impl_registry, services.view_registry)
