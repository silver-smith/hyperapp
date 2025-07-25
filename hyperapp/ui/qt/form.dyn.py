import logging
import weakref

from PySide6 import QtCore, QtWidgets

from hyperapp.boot.htypes import TRecord

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.view import Item, View
from .code.box_layout import BoxLayoutView
from .code.construct_default_form import construct_default_form

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
        return self._adapter.get_value()


async def _form_view_factory(piece, system_fn, ctx, visualizer, editable):
    record_t = pyobj_creg.invite(piece.record_t)
    adapter = htypes.record_adapter.fn_record_adapter(
        record_t=piece.record_t,
        system_fn=mosaic.put(system_fn.piece),
        )
    return await construct_default_form(visualizer, ctx, adapter, record_t, editable=editable)


@mark.view_factory.ui_t
async def form_view_factory(piece, system_fn, ctx, visualizer):
    return await _form_view_factory(piece, system_fn, ctx, visualizer, editable=True)


@mark.view_factory.ui_t
async def readonly_form_view_factory(piece, system_fn, ctx, visualizer):
    return await _form_view_factory(piece, system_fn, ctx, visualizer, editable=False)
