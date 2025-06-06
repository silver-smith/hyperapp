from functools import cached_property

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context_view import ContextView


class LocalServerContextView(ContextView):

    @classmethod
    @mark.view
    def from_piece(cls, piece, ctx, view_reg, local_server_peer):
        base_view = view_reg.invite(piece.base, ctx)
        return cls(local_server_peer, base_view)

    def __init__(self, local_server_peer, base_view):
        super().__init__(base_view, label="Local server")
        self._local_server_peer = local_server_peer

    @property
    def piece(self):
        return htypes.local_server_context.view(
            base=mosaic.put(self._base_view.piece),
            )

    def children_context(self, ctx):
        return ctx.clone_with(
            remote_peer=self._local_server_peer
            )


@mark.global_command
def open_local_server_context(view, state, hook, ctx, view_reg):
    new_view_piece = htypes.local_server_context.view(
        base=mosaic.put(view.piece),
        )
    new_state = htypes.context_view.state(
        base=mosaic.put(state),
        )
    new_view = view_reg.animate(new_view_piece, ctx)
    hook.replace_view(new_view, new_state)
