import logging

from PySide6 import QtWidgets

from . import htypes
from .services import (
    ui_adapter_creg,
    ui_command_factory,
    )

log = logging.getLogger(__name__)


class ViewTextCtl:

    @classmethod
    def from_piece(cls, layout):
        return cls(layout.adapter)

    def __init__(self, adapter_piece):
        self._adapter_piece = adapter_piece

    def construct_widget(self, state, ctx):
        adapter = ui_adapter_creg.invite(self._adapter_piece, ctx)
        w = QtWidgets.QTextBrowser()
        w.setPlainText(adapter.get_text())
        return w

    def widget_state(self, widget):
        # return htypes.text.state(text=widget.toPlainText())
        return htypes.text.state()

    def get_commands(self, layout, widget, wrapper):
        commands = ui_command_factory(layout, self)
        return [command.bind(layout, widget, wrapper) for command in commands]


class EditTextCtl:

    @classmethod
    def from_piece(cls, layout):
        return cls(layout.adapter)

    def __init__(self, adapter_piece):
        self._adapter_piece = adapter_piece

    def construct_widget(self, state, ctx):
        adapter = ui_adapter_creg.invite(self._adapter_piece, ctx)
        w = QtWidgets.QTextEdit()
        w.setPlainText(adapter.get_text())
        return w

    def widget_state(self, widget):
        # return htypes.text.state(text=widget.toPlainText())
        return htypes.text.state()

    def model_state(self, widget):
        # return htypes.text.state(text=widget.toPlainText())
        return htypes.text.state()

    def get_commands(self, layout, widget, wrapper):
        commands = ui_command_factory(layout, self)
        return [command.bind(layout, widget, wrapper) for command in commands]
