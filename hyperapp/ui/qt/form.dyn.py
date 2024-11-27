import logging

from PySide6 import QtWidgets

from hyperapp.common.htypes import TRecord

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.view import Item, View

log = logging.getLogger(__name__)


class FormView(View):

    @classmethod
    @mark.actor.model_view_creg
    def from_piece(cls, piece, model, ctx, visualizer, ui_adapter_creg, model_view_creg):
        adapter = ui_adapter_creg.invite(piece.adapter, model, ctx)
        return cls(visualizer, model_view_creg, piece.adapter, adapter, ctx.lcs)

    def __init__(self, visualizer, model_view_creg, adapter_ref, adapter, lcs):
        super().__init__()
        self._visualizer = visualizer
        self._model_view_creg = model_view_creg
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
            view_piece = self._visualizer(self._lcs, field)
            view = self._model_view_creg.animate(view_piece, field, ctx)
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
        return self._make_state(widget)

    def _make_state(self, widget):
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
            )

    def _model_state(self, widget):
        return self._make_state(widget)

    def items(self):
        return [
            Item(name, view, focusable=True)
            for name, view in self._fields.items()
            ]

    def item_widget(self, widget, idx):
        layout = widget.layout()
        return layout.itemAt(idx*2 + 1).widget()
