from PySide6 import QtCore, QtWidgets

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.view import Item, View


class ContextView(View):

    def __init__(self, base_view, label):
        super().__init__()
        self._base_view = base_view
        self._label = label

    @property
    def piece(self):
        raise NotImplementedError()

    def construct_widget(self, state, ctx):
        if state is not None:
            base_state = web.summon(state.base)
        else:
            base_state = None
        base_widget = self._base_view.construct_widget(base_state, ctx)
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.Direction.TopToBottom, widget,
            contentsMargins=QtCore.QMargins(0, 0, 0, 0),
            )
        label = QtWidgets.QLabel(
            text=self._label,
            frameShape=QtWidgets.QFrame.Panel,
            frameShadow=QtWidgets.QFrame.Raised,
            lineWidth=2,
            margin=3,
            )
        layout.addWidget(label)
        layout.addWidget(base_widget)
        return widget

    def set_current_key(self, widget, key):
        base_widget = self._base_widget(widget)
        self._base_view.set_current_key(base_widget, key)

    def widget_state(self, widget):
        base_widget = self._base_widget(widget)
        base_state = self._base_view.widget_state(base_widget)
        return htypes.context_view.state(
            base=mosaic.put(base_state),
            )

    def get_current(self, widget):
        return 0

    def replace_child_widget(self, widget, idx, new_child_widget):
        assert idx == 0
        layout = widget.layout()
        old_w = layout.itemAt(1).widget()
        layout.replaceWidget(old_w, new_child_widget)
        old_w.deleteLater()

    def replace_child(self, ctx, widget, idx, new_child_view, new_child_widget):
        assert idx == 0
        self._base_view = new_child_view
        self.replace_child_widget(widget, idx, new_child_widget)

    def items(self):
        return [Item('base', self._base_view)]

    def item_widget(self, widget, idx):
        if idx == 0:
            return self._base_widget(widget)
        return super().item_widget(widget, idx)

    def _base_widget(self, widget):
        layout = widget.layout()
        return layout.itemAt(1).widget()
