from functools import cached_property

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mark,
    mosaic,
    view_creg,
    web,
    )
from .code.view import Item, View
from .code.local_server import local_server_peer


class LocalServerContextView(View):

    @classmethod
    def from_piece(cls, piece, ctx):
        base_view = view_creg.invite(piece.base, ctx)
        return cls(base_view)

    def __init__(self, base_view):
        super().__init__()
        self._base_view = base_view

    @property
    def piece(self):
        return htypes.local_server_context.view(
            base=mosaic.put(self._base_view.piece),
            )

    def construct_widget(self, state, ctx):
        if state is not None:
            base_state = web.summon(state.base)
        else:
            base_state = None
        base_widget = self._base_view.construct_widget(base_state, ctx)
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.Direction.TopToBottom, widget)
        layout.addWidget(QtWidgets.QLabel(text="Local server"))
        layout.addWidget(base_widget)
        return widget

    def children_context(self, ctx):
        return ctx.clone_with(
            remote_peer=self._local_server_peer
            )

    @cached_property
    def _local_server_peer(self):
        return local_server_peer()

    def get_current(self, widget):
        return 0

    def widget_state(self, widget):
        base_widget = self._base_widget(widget)
        base_state = self._base_view.widget_state(base_widget)
        return htypes.local_server_context.state(
            base=mosaic.put(base_state),
            )

    def replace_child_widget(self, widget, idx, new_child_widget):
        if idx != 0:
            return super().replace_child_widget(widget, idx, new_child_widget)
        layout = widget.layout()
        old_w = layout.itemAt(1).widget()
        layout.replaceWidget(old_w, new_child_widget)
        old_w.deleteLater()

    def items(self):
        return [Item('base', self._base_view)]

    def item_widget(self, widget, idx):
        if idx == 0:
            return self._base_widget(widget)
        return super().item_widget(widget, idx)

    def _base_widget(self, widget):
        layout = widget.layout()
        return layout.itemAt(1).widget()


@mark.ui_command(htypes.navigator.view)
def open_local_server_context(view, state, hook, ctx):
    new_view_piece = htypes.local_server_context.view(
        base=mosaic.put(view.piece),
        )
    new_state = htypes.local_server_context.state(
        base=mosaic.put(state),
        )
    new_view = view_creg.animate(new_view_piece, ctx)
    hook.replace_view(new_view, new_state)
