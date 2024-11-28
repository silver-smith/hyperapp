import logging

from PySide6 import QtWidgets

from . import htypes
from .code.mark import mark
from .code.view import View

log = logging.getLogger(__name__)


class ViewTextView(View):

    @classmethod
    @mark.actor.model_view_creg
    def from_piece(cls, piece, model, ctx, ui_adapter_creg):
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
        return htypes.text.state(text=self.get_plain_text(widget))

    def primary_parent_context(self, rctx, widget):
        return rctx.clone_with(
            model=self._adapter.model,
            model_state=self._model_state(widget),
            )

    def _model_state(self, widget):
        return self.get_plain_text(widget)

    def get_plain_text(self, widget):
        return widget.toPlainText()


class EditTextView(View):

    @classmethod
    @mark.actor.model_view_creg
    def from_piece(cls, piece, model, ctx, ui_adapter_creg):
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
        if state:
            text = state.text
        else:
            text = self._adapter.get_text()
        w.setPlainText(text)
        return w

    def widget_state(self, widget):
        return htypes.text.state(text=self.get_text(widget))

    def primary_parent_context(self, rctx, widget):
        return rctx.clone_with(
            model=self._adapter.model,
            model_state=self._model_state(widget),
            )

    def _model_state(self, widget):
        return self.get_text(widget)

    def get_text(self, widget):
        return widget.toPlainText()
