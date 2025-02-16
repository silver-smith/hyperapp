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
        for idx, elt in enumerate(self._elements):
            if state:
                elt_state = web.summon(state.elements[idx])
            else:
                elt_state = None
            layout.addWidget(elt.view.construct_widget(elt_state, ctx))
        if state and state.current < len(self._elements):
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

    def add_child(self, ctx, widget, child_view):
        log.info("Box layout: add child: %s", child_view)
        idx = len(self._elements)
        elt_widget = child_view.construct_widget(None, ctx)
        elt = self._Element(child_view, focusable=False, stretch=0)
        self._elements.insert(idx, elt)
        layout = widget.layout()
        layout.addWidget(elt_widget, elt.stretch)
        self._ctl_hook.elements_changed()

    def items(self):
        return [
            Item(f"Item#{idx}", elt.view, focusable=elt.focusable)
            for idx, elt in enumerate(self._elements)
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
def wrap(inner):
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
def add_child_element(view, widget, view_factory, ctx, view_reg, view_factory_reg):
    k = web.summon(view_factory.k)
    factory = view_factory_reg[k]
    last_child = view.child_view(view.children_count - 1)
    # Just in case we want to add a wrapper.
    fn_ctx = ctx.clone_with(
        inner=last_child.piece,
        )
    elt_piece = factory.fn.call(ctx=fn_ctx)
    elt_view = view_reg.animate(elt_piece, ctx)
    view.add_child(ctx, widget, elt_view)
