import logging

from PySide6 import QtWidgets

from . import htypes
from .services import (
    model_view_creg,
    mosaic,
    ui_adapter_creg,
    visualizer,
    web,
    )
from .code.view import Item, View

log = logging.getLogger(__name__)


class FormView(View):

    @classmethod
    def from_piece(cls, piece, model, ctx):
        adapter = ui_adapter_creg.invite(piece.adapter, model, ctx)
        return cls(piece.adapter, adapter, ctx.lcs)

    def __init__(self, adapter_ref, adapter, lcs):
        super().__init__()
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
            view_piece = visualizer(self._lcs, field)
            view = model_view_creg.animate(view_piece, field, ctx)
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

    def get_model(self):
        return self._adapter.model

    def model_state(self, widget):
        return None

    def items(self):
        return [
            Item(name, view, focusable=True)
            for name, view in self._fields.items()
            ]

    def item_widget(self, widget, idx):
        layout = widget.layout()
        return layout.itemAt(idx*2 + 1).widget()
