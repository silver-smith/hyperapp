# panel with commands for current dir and selected elements

import logging
import asyncio
import weakref
from PySide import QtCore, QtGui
from ..common.util import encode_path
from .command import Command

log = logging.getLogger(__name__)


class View(QtGui.QDockWidget):

    def __init__(self, window, locale, resource_resolver):
        QtGui.QDockWidget.__init__(self, 'Commands')
        self.setFeatures(self.NoDockWidgetFeatures)
        self.window = weakref.ref(window)
        self._locale = locale
        self._resource_resolver = resource_resolver
        self.current_dir = None
        self.layout = QtGui.QVBoxLayout(spacing=1)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.addSpacing(10)
        self.setWidget(QtGui.QWidget())
        self.widget().setLayout(self.layout)
        self.dir_buttons = []
        self.elts_buttons = []

    def view_changed(self, window):
        dir = window.get_object()
        self._update_dir_commands(window)
        self._update_elt_commands(window)
        self.current_dir = dir

    def view_commands_changed(self, window, command_kinds):
        if 'element' in command_kinds:
            self._update_elt_commands(window)

    def _update_dir_commands(self, window):
        for btn in self.dir_buttons:
            btn.deleteLater()
        self.dir_buttons = []
        idx = 0
        for cmd in window.get_command_list():
            assert isinstance(cmd, Command), repr(cmd)
            if cmd.kind != 'object': continue
            #if cmd.is_system(): continue
            button = self._make_button(cmd)
            button.pressed.connect(lambda cmd=cmd: asyncio.async(cmd.run()))
            self.layout.insertWidget(idx, button)  # must be inserted before spacing
            self.dir_buttons.append(button)
            idx += 1

    def _update_elt_commands(self, window):
        for btn in self.elts_buttons:
            btn.deleteLater()
        self.elts_buttons = []
        for cmd in window.get_command_list(kinds=['element']):
            assert isinstance(cmd, Command) and cmd.kind == 'element', repr(cmd)
            #if cmd.is_system(): continue
            button = self._make_button(cmd)
            button.pressed.connect(lambda cmd=cmd: asyncio.async(cmd.run()))
            self.layout.addWidget(button)
            self.elts_buttons.append(button)

    def _make_button(self, cmd):
        resource = self._resource_resolver.resolve(cmd.resource_key, self._locale)
        if resource:
            if resource.shortcut_list:
                text = '%s (%s)' % (resource.text, resource.shortcut_list[0])
            else:
                text = resource.text
            description = resource.description
        else:
            text = cmd.id
            description = encode_path(cmd.resource_id)
        button = QtGui.QPushButton(text, focusPolicy=QtCore.Qt.NoFocus)
        button.setToolTip(description)
        button.setEnabled(cmd.is_enabled())
        return button

    def __del__(self):
        log.info('~cmd_pane')
