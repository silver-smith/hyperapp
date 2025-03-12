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
        direction = cls._direction_to_qt(piece.direction)
        elements = cls._data_to_elements(piece.elements, ctx, view_reg)
        return cls(direction, elements)

    @classmethod
    def _data_to_elements(cls, elements, ctx, view_reg):
        return [
            cls._Element(
                view=view_reg.invite_opt(elt.view, ctx),
                focusable=elt.focusable,
                stretch=elt.stretch,
                )
            for elt in elements
            ]

    @staticmethod
    def _direction_to_qt(direction):
        return QtWidgets.QBoxLayout.Direction[direction]

    def __init__(self, direction, elements):
        super().__init__()
        self._direction = direction
        self._elements = elements

    @property
    def piece(self):
        return htypes.box_layout.view(
            direction=self._direction.name,
            elements=self._piece_elements,
            )

    @property
    def _piece_elements(self):
        return tuple(
            htypes.box_layout.element(
                view=mosaic.put(elt.view.piece) if elt.view else None,
                focusable=elt.focusable,
                stretch=elt.stretch,
                )
            for elt in self._elements
            )

    def construct_widget(self, state, ctx):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QBoxLayout(self._direction, widget)
        for idx, elt in enumerate(self._elements):
            if state and elt.view:
                elt_state = web.summon(state.elements[idx])
            else:
                elt_state = None
            if elt.view:
                layout.addWidget(elt.view.construct_widget(elt_state, ctx), stretch=elt.stretch)
            else:
                layout.addStretch(stretch=elt.stretch)
        if state and state.current < len(self._elements):
            w = layout.itemAt(state.current).widget()
            if w:  # None for a stretch.
                w.setFocus()
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
            if w and w.hasFocus():
                return idx
        return 0

    def widget_state(self, widget):
        layout = widget.layout()
        elements = []
        for idx, elt in enumerate(self._elements):
            w = layout.itemAt(idx).widget()
            if elt.view:
                elt_state = elt.view.widget_state(w)
            else:
                elt_state = None
            elements.append(mosaic.put_opt(elt_state))
        return htypes.box_layout.state(
            current=layout.count() - 1,  # TODO
            elements=tuple(elements),
            )

    def replace_child(self, ctx, widget, idx, new_child_view, new_child_widget):
        log.info("Box layout: replace child #%d -> %s / %s", idx, new_child_view, new_child_widget)
        old_elt = self._elements[idx]
        self._elements[idx] = self._Element(new_child_view, old_elt.focusable, old_elt.stretch)
        self.replace_child_widget(widget, idx, new_child_widget)

    def add_child(self, ctx, widget, child_view):
        log.info("Box layout: add child: %s", child_view)
        idx = len(self._elements)
        self._insert_child(idx, ctx, widget, child_view)

    def insert_child(self, idx, ctx, widget, child_view):
        log.info("Box layout: insert child @ #%d: %s", idx, child_view)
        self._insert_child(idx, ctx, widget, child_view)

    def _insert_child(self, idx, ctx, widget, child_view):
        elt_widget = child_view.construct_widget(None, ctx)
        elt = self._Element(child_view, focusable=False, stretch=0)
        layout = widget.layout()
        self._elements.insert(idx, elt)
        layout.insertWidget(idx, elt_widget, elt.stretch)
        self._ctl_hook.elements_changed()

    def items(self):
        return [
            Item(f"Item#{idx}", elt.view, focusable=elt.focusable)
            for idx, elt in enumerate(self._elements)
            if elt.view is not None
            ]

    def item_widget(self, widget, idx):
        layout = widget.layout()
        return layout.itemAt(idx).widget()

    @property
    def children_count(self):
        return len(self._elements)

    def child_view(self, idx):
        return self._elements[idx].view

    def replace_element(self, ctx, widget, idx, view):
        log.info("Box layout: replace element #%d -> %s", idx, view)
        elt_widget = view.construct_widget(None, ctx)
        self.replace_child(ctx, widget, idx, view, elt_widget)
        self._ctl_hook.element_replaced(idx, view, elt_widget)


@mark.ui_command(htypes.box_layout.view)
def unwrap(view, state, hook, ctx):
    log.info("Unwrap box layout: %s / %s", view, state)
    inner_view = view.child_view(0)
    inner_state = web.summon(state.elements[0])
    hook.replace_view(inner_view, inner_state)


@mark.view_factory
def wrap_box_layout(inner):
    log.info("Wrap box layout: %s", inner)
    return htypes.box_layout.view(
        direction='TopToBottom',
        elements=(
            htypes.box_layout.element(
                view=mosaic.put(inner),
                focusable=True,
                stretch=1,
                ),
            ),
        )


@mark.ui_command(htypes.box_layout.view, args=['view_factory'])
def add_element(view, widget, view_factory, ctx, view_reg, view_factory_reg):
    k = web.summon(view_factory.k)
    factory = view_factory_reg[k]
    last_child = view.child_view(view.children_count - 1)
    # Just in case we want to add a wrapper.
    fn_ctx = ctx.clone_with(
        inner=last_child.piece,
        )
    elt_piece = factory.call(fn_ctx)
    elt_view = view_reg.animate(elt_piece, ctx)
    view.add_child(ctx, widget, elt_view)


@mark.ui_command(htypes.box_layout.view, args=['view_factory'])
def insert_element(view, widget, element_idx, view_factory, ctx, view_reg, view_factory_reg):
    k = web.summon(view_factory.k)
    factory = view_factory_reg[k]
    first_child = view.child_view(0)
    # Just in case we want to add a wrapper.
    fn_ctx = ctx.clone_with(
        inner=first_child.piece,
        )
    elt_piece = factory.call(fn_ctx)
    elt_view = view_reg.animate(elt_piece, ctx)
    view.insert_child(element_idx, ctx, widget, elt_view)
