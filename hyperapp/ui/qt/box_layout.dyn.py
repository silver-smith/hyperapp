import logging
from collections import namedtuple

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.list_diff import ListDiff
from .code.view import Item, View

log = logging.getLogger(__name__)


class BoxLayoutView(View):

    _Element = namedtuple('_Element', 'view focusable stretch')

    @classmethod
    @mark.view
    def from_piece(cls, piece, ctx, view_reg):
        elements = [
            cls._Element(
                view=view_reg.invite(elt.view, ctx) if elt.view else None,
                focusable=elt.focusable,
                stretch=elt.stretch,
                )
            for elt in piece.elements
            ]
        direction = cls._direction_to_qt(piece.direction)
        return cls(direction, elements)

    @staticmethod
    def _direction_to_qt(direction):
        return QtWidgets.QBoxLayout.Direction[direction]

    def __init__(self, direction, elements):
        super().__init__()
        self._direction = direction
        self._elements = elements

    @property
    def piece(self):
        elements = tuple(
            htypes.box_layout.element(
                view=mosaic.put(elt.view.piece),
                focusable=elt.focusable,
                stretch=elt.stretch,
                )
            for elt in self._elements
            )
        return htypes.box_layout.view(self._direction.name, elements)

    def construct_widget(self, state, ctx):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QBoxLayout(self._direction, widget)
        for elt, elt_state_ref in zip(self._elements, state.elements):
            elt_state = web.summon(elt_state_ref)
            layout.addWidget(elt.view.construct_widget(elt_state, ctx))
        layout.itemAt(state.current).widget().setFocus()
        return widget

    def replace_child_widget(self, widget, idx, new_child_widget):
        elt = self._elements[idx]
        layout = widget.layout()
        old_w = layout.itemAt(idx).widget()
        layout.replaceWidget(old_w, new_child_widget)
        old_w.deleteLater()

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
            elements=tuple(elements),
            )

    def replace_child(self, ctx, widget, idx, new_child_view, new_child_widget):
        log.info("Box layout: replace child #%d -> %s / %s", idx, new_child_view, new_child_widget)
        old_elt = self._elements[idx]
        self._elements[idx] = self._Element(new_child_view, old_elt.focusable, old_elt.stretch)
        self.replace_child_widget(widget, idx, new_child_widget)

    def items(self):
        return [
            Item(f"Item#{idx}", elt.view, focusable=elt.focusable)
            for idx, elt in enumerate(self._elements)
            ]

    def item_widget(self, widget, idx):
        layout = widget.layout()
        return layout.itemAt(idx).widget()

    def child_view(self, idx):
        return self._elements[idx].view

    def replace_element(self, ctx, widget, idx, view):
        log.info("Box layout: replace element #%d -> %s", idx, view)
        elt_widget = view.construct_widget(None, ctx)
        self.replace_child(ctx, widget, idx, view, elt_widget)
        self._ctl_hook.element_replaced(idx, view, elt_widget)
