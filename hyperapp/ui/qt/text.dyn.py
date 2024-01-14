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
        adapter = ui_adapter_creg.invite(layout.adapter)
        return cls(adapter)

    def __init__(self, adapter):
        self._adapter = adapter

    def construct_widget(self, state, ctx):
        w = QtWidgets.QTextBrowser()
        w.setPlainText(self._adapter.get_text())
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
        adapter = ui_adapter_creg.invite(layout.adapter)
        return cls(adapter)

    def __init__(self, adapter):
        self._adapter = adapter

    def construct_widget(self, state, ctx):
        w = QtWidgets.QTextEdit()
        w.setPlainText(self._adapter.get_text())
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
