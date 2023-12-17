import logging

from PySide6 import QtWidgets

from . import htypes
from .services import (
    ui_command_factory,
    )

log = logging.getLogger(__name__)


class ViewTextCtl:

    @classmethod
    def from_piece(cls, layout):
        ctl = cls()
        commands = ui_command_factory(layout, ctl)
        ctl._commands = commands
        return ctl

    def __init__(self):
        self._commands = None

    def construct_widget(self, state, ctx):
        w = QtWidgets.QTextBrowser()
        w.setPlainText(state.text)
        return w

    def widget_state(self, widget):
        return htypes.text.state(text=widget.toPlainText())

    def bind_commands(self, layout, widget, wrapper):
        return [command.bind(layout, widget, wrapper) for command in self._commands]


class EditTextCtl:

    @classmethod
    def from_piece(cls, layout):
        ctl = cls()
        commands = ui_command_factory(layout, ctl)
        ctl._commands = commands
        return ctl

    def __init__(self):
        self._commands = None

    def construct_widget(self, state, ctx):
        w = QtWidgets.QTextEdit()
        w.setPlainText(state.text)
        return w

    def widget_state(self, widget):
        return htypes.text.state(text=widget.toPlainText())

    def bind_commands(self, layout, widget, wrapper):
        return [command.bind(layout, widget, wrapper) for command in self._commands]
