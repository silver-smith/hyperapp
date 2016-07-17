# panel with commands for current dir and selected elements

import logging
import asyncio
import weakref
from PySide import QtCore, QtGui
from .command import Command

log = logging.getLogger(__name__)


class View(QtGui.QDockWidget):

    def __init__( self, window ):
        QtGui.QDockWidget.__init__(self, 'Commands')
        self.setFeatures(self.NoDockWidgetFeatures)
        self.window = weakref.ref(window)
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
        self.current_dir = dir
        self._update_elements(window.get_current_view(), window.get_selected_elts())

    def selected_elements_changed( self, elts ):
        self._update_elements(self.window().get_current_view(), elts)

    def _update_dir_commands( self, window ):
        for btn in self.dir_buttons:
            btn.deleteLater()
        self.dir_buttons = []
        idx = 0
        for cmd in window.get_object_commands():
            assert isinstance(cmd, Command), repr(cmd)
            #if cmd.is_system(): continue
            button = self._make_button(cmd)
            button.pressed.connect(lambda cmd=cmd: asyncio.async(cmd.run()))
            self.layout.insertWidget(idx, button)  # must be inserted before spacing
            self.dir_buttons.append(button)
            idx += 1

    def _update_elements( self, view, elts ):
        for btn in self.elts_buttons:
            btn.deleteLater()
        self.elts_buttons = []
        if not elts: return
        assert len(elts) == 1  # no multi-select support yet
        elt = elts[0]
        for cmd in elt.commands:
            assert isinstance(cmd, Command), repr(cmd)
            if cmd.is_system(): continue
            button = self._make_button(cmd)
            button.pressed.connect(lambda cmd=cmd: asyncio.async(cmd.run()))
            self.layout.addWidget(button)
            self.elts_buttons.append(button)

    def _make_button( self, cmd ):
        ## if cmd.shortcut:
        ##     text = '%s (%s)' % (cmd.text, cmd.shortcut)
        ## else:
        ##     text = cmd.text
        text = '%s/%s' % (cmd.resource_id, cmd.id)
        button = QtGui.QPushButton(text, focusPolicy=QtCore.Qt.NoFocus)
        ## button.setToolTip(cmd.desc)
        return button

    def __del__( self ):
        log.info('~cmd_pane')
