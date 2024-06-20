from . import htypes
from .services import (
    mark,
    model_view_creg,
    )


@mark.ui_command
def toggle_editable(piece, view, hook, ctx):
    view_piece = view.piece
    if isinstance(view_piece, htypes.text.readonly_view):
        new_view = htypes.text.edit_view(view_piece.adapter)
    elif isinstance(view_piece, htypes.text.edit_view):
        new_view = htypes.text.readonly_view(view_piece.adapter)
    else:
        return
    new_view = model_view_creg.animate(new_view, piece, ctx)
    hook.replace_view(new_view)
