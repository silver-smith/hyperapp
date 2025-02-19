from PySide6 import QtWidgets

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
        layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.Direction.TopToBottom, widget)
        layout.addWidget(QtWidgets.QLabel(text=self._label))
        layout.addWidget(base_widget)
        return widget

    def widget_state(self, widget):
        base_widget = self._base_widget(widget)
        base_state = self._base_view.widget_state(base_widget)
        return htypes.context_view.state(
            base=mosaic.put(base_state),
            )

    def get_current(self, widget):
        return 0

    def replace_child_widget(self, widget, idx, new_child_widget):
        if idx != 0:
            return super().replace_child_widget(widget, idx, new_child_widget)
        layout = widget.layout()
        old_w = layout.itemAt(1).widget()
        layout.replaceWidget(old_w, new_child_widget)
        old_w.deleteLater()

    def items(self):
        return [Item('base', self._base_view)]

    def item_widget(self, widget, idx):
        if idx == 0:
            return self._base_widget(widget)
        return super().item_widget(widget, idx)

    def _base_widget(self, widget):
        layout = widget.layout()
        return layout.itemAt(1).widget()
