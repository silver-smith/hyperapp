from PySide2 import QtWidgets

from hyperapp.common.module import Module

from . import htypes
from .view import View
from .selector import Selector


class SelectorView(QtWidgets.QWidget, View):

    @classmethod
    async def from_piece(cls, piece, object, add_dir_list, mosaic, view_producer):
        list_view = await view_producer.create_view(object.list_object)
        return cls(mosaic, object, list_view)

    def __init__(self, mosaic, selector, list_view):
        QtWidgets.QWidget.__init__(self)
        View.__init__(self)
        self._mosaic = mosaic
        self._selector = selector
        self._list_view = list_view
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Select:"))
        layout.addWidget(list_view.qt_widget)
        self.setLayout(layout)

    def setVisible(self, visible):
        super().setVisible(visible)
        if visible:
            self._list_view.setFocus()

    @property
    def piece(self):
        return htypes.selector_view.selector_view()

    @property
    def state(self):
        list_view_state_ref = self._mosaic.put(self._list_view.state)
        return htypes.selector_view.selector_view_state(list_view_state_ref)

    @state.setter
    def state(self, state):
        list_view_state = self._mosaic.resolve_ref(state.list_view_state_ref).value
        self._list_view.state = list_view_state

    @property
    def object(self):
        return self._selector

    def get_current_child(self):
        return self._list_view
    

class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.lcs.set([htypes.view.view_d('default'), *Selector.dir_list[-1]], htypes.selector_view.selector_view())
        services.view_registry.register_actor(
            htypes.selector_view.selector_view, SelectorView.from_piece, services.mosaic, services.view_producer)
