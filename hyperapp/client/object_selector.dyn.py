from PySide import QtCore, QtGui

from .object import Object
from .view import View
from .module import Module
from ..common.interface import object_selector as object_selector_types


class ObjectSelectorObject(Object):

    impl_id = 'object_selector'

    @classmethod
    def from_state(cls, state):
        return cls()

    def __init__(self):
        Object.__init__(self)

    def get_state(self):
        return object_selector_types.object_selector_object(self.impl_id)


class ObjectSelectorView(View, QtGui.QWidget):

    impl_id = 'object_selector'

    @classmethod
    async def from_state(cls, locale, state, parent, objimpl_registry, view_registry):
        object = await objimpl_registry.resolve(state.object)
        target_view = await view_registry.resolve(locale, state.target)
        return cls(object, target_view)

    def __init__(self, object, target_view):
        QtGui.QWidget.__init__(self)
        View.__init__(self)
        self.object = object
        self.target_view = target_view
        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel('Select object'))
        layout.addWidget(target_view.get_widget())
        self.setLayout(layout)

    def get_state(self):
        target_handle = self.target_view.get_state()
        object = self.object.get_state()
        return object_selector_types.object_selector_view(self.impl_id, object, target_handle)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        services.objimpl_registry.register(ObjectSelectorObject.impl_id, ObjectSelectorObject.from_state)
        services.view_registry.register(ObjectSelectorView.impl_id, ObjectSelectorView.from_state, services.objimpl_registry, services.view_registry)
