from functools import cached_property

from . import htypes
from .services import (
    mark,
    mosaic,
    view_creg,
    )
from .code.context_view import ContextView
from .code.local_server import local_server_peer


class LocalServerContextView(ContextView):

    @classmethod
    def from_piece(cls, piece, ctx):
        base_view = view_creg.invite(piece.base, ctx)
        return cls(base_view)

    def __init__(self, base_view):
        super().__init__(base_view, label="Local server")

    @property
    def piece(self):
        return htypes.local_server_context.view(
            base=mosaic.put(self._base_view.piece),
            )

    def children_context(self, ctx):
        return ctx.clone_with(
            remote_peer=self._local_server_peer
            )

    @cached_property
    def _local_server_peer(self):
        return local_server_peer()

    def widget_state(self, widget):
        base_widget = self._base_widget(widget)
        base_state = self._base_view.widget_state(base_widget)
        return htypes.local_server_context.state(
            base=mosaic.put(base_state),
            )


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
