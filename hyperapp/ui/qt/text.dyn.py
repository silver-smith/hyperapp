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
    def from_piece(cls, piece):
        return cls(piece.adapter)

    def __init__(self, adapter_ref):
        self._adapter_ref = adapter_ref

    @property
    def piece(self):
        return htypes.text.readonly_view(self._adapter_ref)

    def construct_widget(self, state, ctx):
        adapter = ui_adapter_creg.invite(self._adapter_ref, ctx)
        w = QtWidgets.QTextBrowser()
        w.setPlainText(adapter.get_text())
        return w

    def widget_state(self, widget):
        # return htypes.text.state(text=widget.toPlainText())
        return htypes.text.state()


class EditTextView(View):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.adapter)

    def __init__(self, adapter_ref):
        self._adapter_ref = adapter_ref

    @property
    def piece(self):
        return htypes.text.edit_layout(self._adapter_ref)

    def construct_widget(self, state, ctx):
        adapter = ui_adapter_creg.invite(self._adapter_ref, ctx)
        w = QtWidgets.QTextEdit()
        w.setPlainText(adapter.get_text())
        return w

    def widget_state(self, widget):
        # return htypes.text.state(text=widget.toPlainText())
        return htypes.text.state()

    def model_state(self, widget):
        # return htypes.text.state(text=widget.toPlainText())
        return htypes.text.state()
