import logging
from functools import partial

from PySide6 import QtWidgets

log = logging.getLogger(__name__)

from . import htypes
from .code.view import View


class MenuBarView(View):

    @classmethod
    def from_piece(cls, piece):
        return cls()

    def __init__(self):
        super().__init__()

    @property
    def piece(self):
        return htypes.menu_bar.view()

    def construct_widget(self, state, ctx):
        w =  QtWidgets.QMenuBar()
        menu = QtWidgets.QMenu('&All')
        w.addMenu(menu)
        ctx.command_hub.subscribe(partial(self.commands_changed, w))
        return w

    def widget_state(self, widget):
        return htypes.menu_bar.state()

    def commands_changed(self, w, removed_commands, added_commands):
        [menu_action] = w.actions()
        menu = menu_action.menu()
        for command in removed_commands:
            menu.removeAction(command.action)
        for command in added_commands:
            menu.addAction(command.action)
