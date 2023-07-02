from . import htypes
from .services import (
    mark,
    mosaic,
    )


@mark.param.Window
def piece():
    return htypes.window.window(
        menu_bar_ref=mosaic.put(htypes.menu_bar.menu_bar()),
        command_pane_ref=mosaic.put(htypes.command_pane.command_pane()),
        central_view_ref=mosaic.put('phony view'),
        size=htypes.window.size(100, 100),
        pos=htypes.window.pos(10, 10),
        )
