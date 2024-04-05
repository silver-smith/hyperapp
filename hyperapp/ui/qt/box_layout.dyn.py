import logging
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

log = logging.getLogger(__name__)


class BoxLayoutView(View):

    _Element = namedtuple('_Element', 'view focusable stretch')

    @classmethod
    def from_piece(cls, piece):
        elements = [
            cls._Element(
                view=ui_ctl_creg.invite(elt.view) if elt.view else None,
                focusable=elt.focusable,
                stretch=elt.stretch,
                )
            for elt in piece.elements
            ]
        direction = QtWidgets.QBoxLayout.Direction[piece.direction]
        return cls(direction, elements)

    def __init__(self, direction, elements):
        super().__init__()
        self._direction = direction
        self._elements = elements

    @property
    def piece(self):
        elements = [
            htypes.box_layout.element(
                view=mosaic.put(elt.view.piece),
                focusable=elt.focusable,
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
            elements=elements,
            )

    def items(self):
        return [
            Item(f"Item#{idx}", elt.view, focusable=elt.focusable)
            for idx, elt in enumerate(self._elements)
            ]

    def item_widget(self, widget, idx):
        layout = widget.layout()
        return layout.itemAt(idx).widget()

    def apply(self, ctx, widget, diff):
        log.info("Box layout: apply: %s", diff)
        if isinstance(diff.piece, ListDiff.Replace):
            idx = diff.piece.idx
            view = ui_ctl_creg.animate(diff.piece.item)
            old_elt = self._elements[idx]
            self._elements[idx] = self._Element(view, old_elt.focusable, old_elt.stretch)
            elt_widget = view.construct_widget(None, ctx)
            self.replace_child_widget(widget, idx, elt_widget)
            self._ctl_hook.replace_item_element(idx, view, elt_widget)
        else:
            raise NotImplementedError(f"Not implemented: tab.apply({diff.piece})")

    def child_view(self, idx):
        return self._elements[idx].view
