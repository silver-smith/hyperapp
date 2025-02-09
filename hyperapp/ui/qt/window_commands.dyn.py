import logging

from PySide6 import QtWidgets

from . import htypes
from .code.mark import mark

log = logging.getLogger(__name__)

DUP_OFFSET = htypes.window.pos(150, 50)


@mark.ui_command(htypes.window.view)
async def duplicate_window(root, view, state):
    log.info("Duplicate window: %s / %s", view, state)
    new_state = htypes.window.state(
        menu_bar_state=state.menu_bar_state,
        central_view_state=state.central_view_state,
        size=state.size,
        pos=htypes.window.pos(
            x=state.pos.x + DUP_OFFSET.x,
            y=state.pos.y + DUP_OFFSET.y,
            ),
        )
    await root.create_window(view.piece, new_state)


@mark.ui_command(htypes.window.view)
def quit(hook):
    hook.save_state()
    QtWidgets.QApplication.quit()
