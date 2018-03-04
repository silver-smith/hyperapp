import logging
from collections import OrderedDict
from PySide import QtCore, QtGui

from ..common.interface import form as form_types
from .util import call_after
from .module import Module
from .object import Object
from .view import View

log = logging.getLogger(__name__)


class FormObject(Object):

    impl_id = 'form'

    @classmethod
    def from_state(cls, field_object_map, state):
        return cls(field_object_map, state)

    def __init__(self, field_object_map, state):
        super().__init__()

    def get_title(self):
        return 'form'

    def get_state(self):
        return form_types.form_object(self.impl_id)


class FormView(View, QtGui.QWidget):

    impl_id = 'form'

    @classmethod
    async def from_state(cls, locale, state, parent, objimpl_registry, view_registry):
        field_view_map = OrderedDict()
        for field in state.field_list:
            field_view_map[field.id] = await view_registry.resolve(locale, field.view)
        object = FormObject.from_state({id: view.get_object() for id, view in field_view_map.items()}, state.object)
        return cls(parent, object, field_view_map, state.current_field_id)

    def __init__(self, parent, object, field_view_map, current_field_id):
        QtGui.QWidget.__init__(self)
        View.__init__(self, parent)
        self._object = object
        self._field_view_map = field_view_map
        layout = QtGui.QVBoxLayout()
        for id, field_view in field_view_map.items():
            self._construct_field(layout, id, field_view, focus_it = id==current_field_id)
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
        if focus_it:
            call_after(field_view.ensure_has_focus)


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(services)
        # hack to just make application storage and dynamic module registry's get_dynamic_module_id happy, not use otherwise:
        services.objimpl_registry.register(FormObject.impl_id, FormObject.from_state)
        services.view_registry.register(FormView.impl_id, FormView.from_state, services.objimpl_registry, services.view_registry)
