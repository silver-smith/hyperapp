import logging

from PySide6 import QtWidgets

from . import htypes
from .services import (
    ui_adapter_creg,
    )
from .code.view import View

log = logging.getLogger(__name__)


class ViewTextView(View):

    @classmethod
    def from_piece(cls, piece, model, ctx):
        adapter = ui_adapter_creg.invite(piece.adapter, model, ctx)
        return cls(piece.adapter, adapter)

    def __init__(self, adapter_ref, adapter):
        super().__init__()
        self._adapter_ref = adapter_ref
        self._adapter = adapter

    @property
    def piece(self):
        return htypes.text.readonly_view(self._adapter_ref)

    def construct_widget(self, state, ctx):
        w = QtWidgets.QTextBrowser()
        w.setPlainText(self._adapter.get_text())
        return w

    def widget_state(self, widget):
        # return htypes.text.state(text=widget.toPlainText())
        return htypes.text.state()

    def primary_parent_context(self, rctx, widget):
        return rctx.clone_with(
            model=self._adapter.model,
            model_state=self._model_state(widget),
            )

    def _model_state(self, widget):
        # return htypes.text.state(text=widget.toPlainText())
        return htypes.text.state()


class EditTextView(View):

    @classmethod
    def from_piece(cls, piece, model, ctx):
        adapter = ui_adapter_creg.invite(piece.adapter, model, ctx)
        return cls(piece.adapter, adapter)

    def __init__(self, adapter_ref, adapter):
        super().__init__()
        self._adapter_ref = adapter_ref
        self._adapter = adapter

    @property
    def piece(self):
        return htypes.text.edit_view(self._adapter_ref)

    def construct_widget(self, state, ctx):
        w = QtWidgets.QTextEdit()
        w.setPlainText(self._adapter.get_text())
        return w

    def widget_state(self, widget):
        # return htypes.text.state(text=widget.toPlainText())
        return htypes.text.state()

    def primary_parent_context(self, rctx, widget):
        return rctx.clone_with(
            model=self._adapter.model,
            model_state=self._model_state(widget),
            )

    def _model_state(self, widget):
        # return htypes.text.state(text=widget.toPlainText())
        return htypes.text.state()
