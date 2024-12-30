from PySide6 import QtWidgets

from . import htypes
from .code.mark import mark
from .code.view import View


class LabelView(View):

    @classmethod
    @mark.view
    def from_piece(cls, piece, ctx):
        return cls(piece.text)

    def __init__(self, text):
        super().__init__()
        self._text = text

    @property
    def piece(self):
        return htypes.label.view(self._text)

    def construct_widget(self, state, ctx):
        return QtWidgets.QLabel(text=self._text)

    def widget_state(self, widget):
        return htypes.label.state()
