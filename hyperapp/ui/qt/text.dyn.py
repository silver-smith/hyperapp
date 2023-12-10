import logging

from PySide6 import QtWidgets

from . import htypes

log = logging.getLogger(__name__)


class ViewTextCtl:

    @classmethod
    def from_piece(cls, layout):
        return cls()

    def __init__(self):
        pass

    def construct_widget(self, state, ctx):
        w = QtWidgets.QTextBrowser()
        w.setPlainText(state.text)
        return w

    def widget_state(self, widget):
        return htypes.text.state(text=widget.toPlainText())

    def bind_commands(self, widget, wrapper):
        return [command.bind(widget, wrapper) for command in self._commands]


class EditTextCtl:

    @classmethod
    def from_piece(cls, layout):
        return cls()

    def __init__(self):
        pass

    def construct_widget(self, state, ctx):
        w = QtWidgets.QTextEdit()
        w.setPlainText(state.text)
        return w

    def widget_state(self, widget):
        return htypes.text.state(text=widget.toPlainText())

    def bind_commands(self, widget, wrapper):
        return [command.bind(widget, wrapper) for command in self._commands]
