import logging
from collections import namedtuple

from PySide6 import QtCore, QtWidgets

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.list_diff import ListDiff
from .code.view import Item, View

log = logging.getLogger(__name__)


class SplitterView(View):

    @classmethod
    @mark.view
    def from_piece(cls, piece, ctx, view_reg):
        elements = [
            view_reg.invite(elt, ctx)
            for elt in piece.elements
            ]
        orientation = cls._orientation_to_qt(piece.orientation)
        return cls(orientation, elements)

    @staticmethod
    def _orientation_to_qt(orientation):
        return QtCore.Qt.Orientation[orientation]

    def __init__(self, orientation, elements):
        super().__init__()
        self._orientation = orientation
        self._elements = elements  # View list.

    @property
    def piece(self):
        elements = tuple(
            mosaic.put(view.piece)
            for view in self._elements
            )
        return htypes.splitter.view(self._orientation.name, elements)

    def construct_widget(self, state, ctx):
        widget = QtWidgets.QSplitter(self._orientation)
        for idx, view in enumerate(self._elements):
            if state:
                elt_state = web.summon(state.elements[idx])
            else:
                elt_state = None
            elt_widget = view.construct_widget(elt_state, ctx)
            widget.addWidget(elt_widget)
        if state and state.current < len(self._elements):
            widget.widget(state.current).setFocus()
        return widget

    def replace_child_widget(self, widget, idx, new_child_widget):
        widget.replaceWidget(idx, new_child_widget)

    def get_current(self, widget):
        for idx in range(len(self._elements)):
            w = widget.widget(idx)
            if w.hasFocus():
                return idx
        return 0

    def widget_state(self, widget):
        elements = []
        for idx, view in enumerate(self._elements):
            elt_widget = widget.widget(idx)
            elt_state = view.widget_state(elt_widget)
            elements.append(mosaic.put(elt_state))
        return htypes.splitter.state(
            current=self.get_current(widget),
            elements=tuple(elements),
            )

    def replace_child(self, ctx, widget, idx, new_child_view, new_child_widget):
        log.info("Splitter: replace child #%d -> %s / %s", idx, new_child_view, new_child_widget)
        self._elements[idx] = new_child_view
        self.replace_child_widget(widget, idx, new_child_widget)

    def add_child(self, ctx, widget, child_view):
        log.info("Splitter: add child: %s", child_view)
        elt_widget = child_view.construct_widget(None, ctx)
        self._elements.append(child_view)
        widget.addWidget(elt_widget)
        self._ctl_hook.elements_changed()

    def items(self):
        return [
            Item(f"Item#{idx}", view, focusable=True)
            for idx, view in enumerate(self._elements)
            ]

    def item_widget(self, widget, idx):
        return widget.widget(idx)

    @property
    def children_count(self):
        return len(self._elements)

    def child_view(self, idx):
        return self._elements[idx]

    def replace_element(self, ctx, widget, idx, view):
        log.info("Splitter: replace element #%d -> %s", idx, view)
        elt_widget = view.construct_widget(None, ctx)
        self.replace_child(ctx, widget, idx, view, elt_widget)
        self._ctl_hook.element_replaced(idx, view, elt_widget)


@mark.ui_command(htypes.splitter.view)
def unwrap(view, state, hook, ctx):
    log.info("Unwrap splitter: %s / %s", view, state)
    inner_view = view.child_view(0)
    inner_state = web.summon(state.elements[0])
    hook.replace_view(inner_view, inner_state)


@mark.view_factory
def wrap_splitter(inner):
    log.info("Wrap splitter: %s", inner)
    return htypes.splitter.view(
        orientation='Horizontal',
        elements=(
            mosaic.put(inner),
            ),
        )
