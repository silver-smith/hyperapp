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


@mark.view_factory
def label_view():
    return htypes.label.view(
        text="Label text not set",
        )


@mark.ui_command(htypes.label.view, args=['text'])
def set_label_text(piece, text, hook, ctx, view_reg):
    new_piece = htypes.label.view(
        text=text,
        )
    new_view = view_reg.animate(new_piece, ctx)
    hook.replace_view(new_view)
