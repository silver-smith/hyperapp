from collections import namedtuple

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mark,
    mosaic,
    ui_ctl_creg,
    web,
    )
from .code.list_diff import ListDiff
from .code.view import Diff, Item, View


class BoxLayoutView(View):

    _Element = namedtuple('_Element', 'view stretch')

    @classmethod
    def from_piece(cls, piece):
        elements = [
            cls._Element(
                view=ui_ctl_creg.invite(elt.view) if elt.view else None,
                stretch=elt.stretch,
                )
            for elt in piece.elements
            ]
        direction = QtWidgets.QBoxLayout.Direction[piece.direction]
        return cls(direction, elements)

    def __init__(self, direction, elements):
        self._direction = direction
        self._elements = elements

    @property
    def piece(self):
        elements = [
            htypes.box_layout.element(
                view=mosaic.put(elt.view.piece),
                stretch=elt.stretch,
                )
            for elt in self._elements
            ]
        return htypes.box_layout.view(self._direction.name, elements)

    def construct_widget(self, state, ctx):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QBoxLayout(self._direction, widget)
        for elt, elt_state_ref in zip(self._elements, state.elements):
            elt_state = web.summon(elt_state_ref)
            layout.addWidget(elt.view.construct_widget(elt_state, ctx))
        layout.itemAt(state.current).widget().setFocus()
        return widget

    def replace_widget(self, ctx, widget, idx):
        elt = self._elements[idx]
        state = None  # TODO: Navigator apply should return new state.
        layout = widget.layout()
        w = elt.view.construct_widget(state, ctx)
        old_w = layout.itemAt(idx).widget()
        layout.replaceWidget(old_w, w)
        old_w.deleteLater()
        return w

    def get_current(self, widget):
        layout = widget.layout()
        for idx in range(layout.count()):
            w = layout.itemAt(idx).widget()
            if not w.focusPolicy():  # Qt.NoFocus == 0
                continue
            return idx
        return 0

    def widget_state(self, widget):
        layout = widget.layout()
        elements = []
        for idx, elt in enumerate(self._elements):
            w = layout.itemAt(idx).widget()
            elt_state = elt.view.widget_state(w)
            elements.append(mosaic.put(elt_state))
        return htypes.box_layout.state(
            current=layout.count() - 1,  # TODO
            elements=elements,
            )

    def items(self, widget):
        layout = widget.layout()
        return [
            Item(f"Item#{idx}", elt.view, layout.itemAt(idx).widget())
            for idx, elt in enumerate(self._elements)
            ]

    def child_view(self, idx):
        return self._elements[idx].view

    def child_widget(self, widget, idx):
        layout = widget.layout()
        return layout.itemAt(idx).widget()
