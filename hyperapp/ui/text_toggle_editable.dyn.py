from . import htypes
from .code.mark import mark


@mark.ui_command(htypes.text.readonly_view)
@mark.ui_command(htypes.text.edit_view)
def toggle_editable(piece, view, hook, ctx, view_reg):
    view_piece = view.piece
    if isinstance(view_piece, htypes.text.readonly_view):
        new_view = htypes.text.edit_view(view_piece.adapter)
    elif isinstance(view_piece, htypes.text.edit_view):
        new_view = htypes.text.readonly_view(view_piece.adapter)
    else:
        return
    new_view = view_reg.animate(new_view, ctx)
    hook.replace_view(new_view)
