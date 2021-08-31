# panel with commands for current dir and selected elements

import logging
import asyncio
import weakref

from PySide2 import QtCore, QtWidgets

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class CommandPane(QtWidgets.QDockWidget):

    @classmethod
    async def from_state(cls, state, command_hub, lcs):
        return cls(lcs, command_hub)

    def __init__(self, lcs, command_hub):
        QtWidgets.QDockWidget.__init__(self, 'Commands')
        self.setFeatures(self.NoDockWidgetFeatures)
        self._lcs = lcs
        self._layout = QtWidgets.QVBoxLayout(spacing=1)
        self._layout.setAlignment(QtCore.Qt.AlignTop)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.addSpacing(10)
        self.setWidget(QtWidgets.QWidget())
        self.widget().setLayout(self._layout)
        self._dir_buttons = []
        self._element_buttons = []
        command_hub.subscribe(self)

    @property
    def state(self):
        return htypes.command_pane.command_pane()

    # command hum observer method
    def commands_changed(self, kind, command_list):
        if kind == 'object':
            self._update_dir_commands(command_list)
        if kind == 'element':
            self._update_element_commands(command_list)

    def _update_dir_commands(self, command_list):
        for button in self._dir_buttons:
            button.deleteLater()
        self._dir_buttons.clear()
        idx = 0
        for command in command_list:
            if command.kind != 'object':
                continue
            button = self._make_button(command, set_shortcuts=True)
            self._layout.insertWidget(idx, button)  # must be inserted before spacing
            self._dir_buttons.append(button)
            idx += 1

    def _update_element_commands(self, command_list):
        for button in self._element_buttons:
            button.deleteLater()
        self._element_buttons.clear()
        for command in command_list:
            button = self._make_button(command, set_shortcuts=True)
            self._layout.addWidget(button)
            self._element_buttons.append(button)

    def _make_button(self, command, set_shortcuts):
        text = command.name
        shortcut = self._lcs.get([*command.dir, htypes.command.command_shortcut_d()])
        is_default = False
        if shortcut:
            text += f" ({shortcut})"
        button = QtWidgets.QPushButton(text, focusPolicy=QtCore.Qt.NoFocus)
        # button.setToolTip(description)
        # button.setEnabled(command.is_enabled())
        button.pressed.connect(lambda command=command: asyncio.ensure_future(command.run()))
        if set_shortcuts and shortcut:
            button.setShortcut(shortcut)
        if is_default:
            button.setShortcut('Return')
        return button

    # def __del__(self):
    #     log.info('~command_pane')


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.view_registry.register_actor(
            htypes.command_pane.command_pane, CommandPane.from_state, services.lcs)
