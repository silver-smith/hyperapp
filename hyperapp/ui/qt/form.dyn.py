import logging
import weakref

from PySide6 import QtCore, QtWidgets

from hyperapp.boot.htypes import TRecord

from . import htypes
from .services import (
    deduce_t,
    mosaic,
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
        name_to_value = {}
        for idx, (name, view) in enumerate(self._fields.items()):
            w = self.item_widget(widget, idx)
            name_to_value[name] = view.get_value(w)
        return self._adapter.record_t(**name_to_value)


def construct_default_form(visualizer, ctx, adapter, record_t):
    element_list = []
    for name, t in record_t.fields.items():
        field_view = visualizer(ctx, t)
        wrapped_view = htypes.model_field_wrapper_view.view(
            base_view=mosaic.put(field_view),
            field_name=name,
            )
        element = htypes.box_layout.element(
            view=mosaic.put(wrapped_view),
            focusable=True,
            stretch=1,
            )
        element_list.append(element)
    return htypes.form.view(
        direction='TopToBottom',
        elements=tuple(element_list),
        adapter=mosaic.put(adapter),
        )
