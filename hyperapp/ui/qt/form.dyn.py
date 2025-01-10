import logging
import weakref

from PySide6 import QtWidgets

from hyperapp.boot.htypes import TRecord

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.view import Item, View

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


class FormView(View):

    @classmethod
    @mark.view
    def from_piece(cls, piece, model, ctx, visualizer, ui_adapter_creg, view_reg):
        adapter = ui_adapter_creg.invite(piece.adapter, model, ctx)
        return cls(visualizer, view_reg, piece.adapter, adapter, ctx.lcs)

    def __init__(self, visualizer, view_reg, adapter_ref, adapter, lcs):
        super().__init__()
        self._visualizer = visualizer
        self._view_reg = view_reg
        self._adapter_ref = adapter_ref
        self._adapter = adapter
        self._lcs = lcs
        self._fields = {}  # name -> view

    @property
    def piece(self):
        return htypes.form.view(self._adapter_ref)

    def construct_widget(self, state, ctx):
        if state is not None:
            field_state = {
                rec.name: web.summon(rec.value)
                for rec in state.fields
                }
        else:
            field_state = {}
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        for name, t in self._adapter.record_t.fields.items():
            layout.addWidget(QtWidgets.QLabel(text=name))
            field = self._adapter.get_field(name)
            view_piece = self._visualizer(self._lcs, ctx, field)
            model_ctx = ctx.clone_with(model=field)
            view = self._view_reg.animate(view_piece, model_ctx)
            fs = field_state.get(name)
            w = view.construct_widget(fs, ctx)
            self._fields[name] = view
            layout.addWidget(w)
        return widget

    def get_current(self, widget):
        layout = widget.layout()
        for idx in range(len(self._fields)):
            w = self.item_widget(widget, idx)
            if w.hasFocus():
                return idx
        return 0

    def widget_state(self, widget):
        field_list = []
        for idx, (name, view) in enumerate(self._fields.items()):
            w = self.item_widget(widget, idx)
            state = view.widget_state(w)
            field = htypes.form.field(name, mosaic.put(state))
            field_list.append(field)
        return htypes.form.state(tuple(field_list))

    def primary_parent_context(self, rctx, widget):
        return rctx.clone_with(
            model=self._adapter.model,
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
        
    def items(self):
        return [
            Item(name, view, focusable=True)
            for name, view in self._fields.items()
            ]

    def item_widget(self, widget, idx):
        layout = widget.layout()
        return layout.itemAt(idx*2 + 1).widget()
