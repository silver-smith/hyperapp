import asyncio
from functools import partial

from PySide6 import QtGui, QtWidgets


class MenuBarCtl:

    @classmethod
    def from_piece(cls, layout):
        return cls()

    def __init__(self):
        pass

    def construct_widget(self, state, ctx):
        w = QtWidgets.QMenuBar()
        menu = QtWidgets.QMenu('&All')
        for command in ctx.commands:
            self._add_action(menu, command)
        w.addMenu(menu)
        return w

    def _add_action(self, menu, command):
        action = QtGui.QAction(command.name, menu)
        action.triggered.connect(partial(self._run_command, command))
        menu.addAction(action)

    def _run_command(self, command):
        asyncio.create_task(command.run())
