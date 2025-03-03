import logging
import weakref

from PySide6 import QtCore, QtWidgets

from hyperapp.boot.htypes import TRecord

from . import htypes
from .services import (
    deduce_t,
    mosaic,
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


def construct_default_form(visualizer, ctx, record_adapter, record_t):
    element_list = []
    for name, t in record_t.fields.items():
        label_view = htypes.label.view(name)
        label_element = htypes.box_layout.element(
            view=mosaic.put(label_view),
            focusable=False,
            stretch=0,
            )
        field_adapter = htypes.record_field_adapter.record_field_adapter(
            record_adapter=mosaic.put(record_adapter),
            field_name=name,
            )
        field_view = htypes.line_edit.edit_view(
            adapter=mosaic.put(field_adapter),
            )
        element = htypes.box_layout.element(
            view=mosaic.put(field_view),
            focusable=True,
            stretch=0,
            )
        element_list += [label_element, element]
    return htypes.form.view(
        direction='TopToBottom',
        elements=tuple(element_list),
        adapter=mosaic.put(record_adapter),
        )
