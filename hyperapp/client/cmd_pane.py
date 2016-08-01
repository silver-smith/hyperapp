# panel with commands for current dir and selected elements

import logging
import asyncio
import weakref
from PySide import QtCore, QtGui
from .command import Command

log = logging.getLogger(__name__)


class View(QtGui.QDockWidget):

    def __init__( self, window, locale, resources_registry ):
        QtGui.QDockWidget.__init__(self, 'Commands')
        self.setFeatures(self.NoDockWidgetFeatures)
        self.window = weakref.ref(window)
        self._locale = locale
        self._resources_registry = resources_registry
        self.current_dir = None
        self.layout = QtGui.QVBoxLayout(spacing=1)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.addSpacing(10)
        self.setWidget(QtGui.QWidget())
        self.widget().setLayout(self.layout)
        self.dir_buttons = []
        self.elts_buttons = []

    def view_changed( self, window ):
        dir = window.get_object()
        self._update_dir_commands(window)
        self._update_elt_commands(window)
        self.current_dir = dir

    def view_commands_changed( self, window, command_kinds ):
        if 'element' in command_kinds:
            self._update_elt_commands(window)

    def _update_dir_commands( self, window ):
        for btn in self.dir_buttons:
            btn.deleteLater()
        self.dir_buttons = []
        idx = 0
        for cmd in window.get_commands():
            assert isinstance(cmd, Command), repr(cmd)
            if cmd.kind != 'object': continue
            #if cmd.is_system(): continue
            button = self._make_button(cmd)
            button.pressed.connect(lambda cmd=cmd: asyncio.async(cmd.run()))
            self.layout.insertWidget(idx, button)  # must be inserted before spacing
            self.dir_buttons.append(button)
            idx += 1

    def _update_elt_commands( self, window ):
        for btn in self.elts_buttons:
            btn.deleteLater()
        self.elts_buttons = []
        for cmd in window.get_commands():
            assert isinstance(cmd, Command), repr(cmd)
            if cmd.kind != 'element': continue
            #if cmd.is_system(): continue
            button = self._make_button(cmd)
            button.pressed.connect(lambda cmd=cmd: asyncio.async(cmd.run()))
            self.layout.addWidget(button)
            self.elts_buttons.append(button)

    def _make_button( self, cmd ):
        desc = ''
        resources = self._resources_registry.resolve(cmd.resource_id, self._locale)
        if resources:
            for res in resources.commands:
                if res.id == cmd.id:
                    if res.shortcuts:
                        text = '%s (%s)' % (res.text, res.shortcuts[0])
                    else:
                        text = res.text
                    desc = res.desc
                    break
            else:
                print([rc.id for rc in resources.commands])
                assert False, 'Resource %r does not contain command %r' % (cmd.resource_id, cmd.id)
        else:
            text = '%s/%s' % (cmd.resource_id, cmd.id)
        button = QtGui.QPushButton(text, focusPolicy=QtCore.Qt.NoFocus)
        button.setToolTip(desc)
        return button

    def __del__( self ):
        log.info('~cmd_pane')
