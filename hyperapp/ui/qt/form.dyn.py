import logging
import weakref

from PySide6 import QtCore, QtWidgets

from hyperapp.boot.htypes import TRecord

from . import htypes
from .services import (
    deduce_t,
    web,
    )
from .code.mark import mark
from .code.view import Item, View
from .code.box_layout import BoxLayoutView

log = logging.getLogger(__name__)


class FormInput:

    def __init__(self, view, widget):
        self._view = view
        self._widget_wr = weakref.ref(widget)

    def get_value(self):
        widget = self._widget_wr()
        if not widget:
            raise RuntimeError(f"Form input: widget for {self._view} is gone")
        return self._view.get_value(widget)


class FormView(BoxLayoutView):

    @classmethod
    @mark.view
    def from_piece(cls, piece, model, ctx, ui_adapter_creg, view_reg):
        direction = cls._direction_to_qt(piece.direction)
        elements = cls._data_to_elements(piece.elements, ctx, view_reg)
        adapter = ui_adapter_creg.invite(piece.adapter, model, ctx)
        return cls(direction, elements, piece.adapter, adapter)

    def __init__(self, direction, elements, adapter_ref, adapter):
        super().__init__(direction, elements)
        self._adapter_ref = adapter_ref
        self._adapter = adapter

    @property
    def piece(self):
        return htypes.form.view(
            direction=self._direction.name,
            elements=self._piece_elements,
            adapter=self._adapter_ref
            )

    def primary_parent_context(self, rctx, widget):
        return rctx.clone_with(
            model_state=self._model_state(widget),
            input=FormInput(self, widget),
            )

    def _model_state(self, widget):
        return self.get_value(widget)

    def get_value(self, widget):
        return self._adapter.value


@mark.ui_command(args=['view_factory'])
def add_element(view, widget, view_factory, ctx, view_reg, view_factory_reg):
    k = web.summon(view_factory.k)
    factory = view_factory_reg[k]
    first_child = view.child_view(0)
    # Just in case we want to add a wrapper.
    fn_ctx = ctx.clone_with(
        inner=first_child.piece,
        )
    elt_piece = factory.call(fn_ctx)
    elt_view = view_reg.animate(elt_piece, ctx)
    view.add_child(ctx, widget, elt_view)


@mark.ui_command(args=['view_factory'])
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


@mark.ui_command
def remove_element(view, widget, element_idx):
    view.remove_child(element_idx, widget)
