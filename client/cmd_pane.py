# panel with commands for current dir and selected elements

import weakref
from PySide import QtCore, QtGui
#from object import collect_objs_commands, cmd_elements_to_args
from command import get_dir_commands


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
        dir = window.current_dir()
        self._update_dir(dir)
        self.current_dir = dir
        self._update_elts(window.selected_elts())

    def selected_elements_changed( self, elts ):
        self._update_elts(elts)

    def _update_dir( self, dir ):
        for btn in self.dir_buttons:
            btn.deleteLater()
        self.dir_buttons = []
        if dir is None: return
        idx = 0
        for cmd in get_dir_commands(dir):
            if not cmd.enabled: continue
            btn = self._make_btn(cmd)
            btn.pressed.connect(lambda cmd=cmd, dir=dir: self._on_btn_pressed(cmd, dir))
            self.layout.insertWidget(idx, btn)  # must be inserted before spacing
            self.dir_buttons.append(btn)
            idx += 1

    def _update_elts( self, elts ):
        for btn in self.elts_buttons:
            btn.deleteLater()
        self.elts_buttons = []
        if not elts: return
        for cmd in collect_objs_commands(elts):
            if not cmd.enabled: continue
            btn = self._make_btn(cmd)
            args = cmd_elements_to_args(cmd, elts)
            btn.pressed.connect(lambda cmd=cmd, args=args: self._on_btn_pressed(cmd, *args))
            self.layout.addWidget(btn)
            self.elts_buttons.append(btn)

    def _make_btn( self, cmd ):
        if cmd.shortcut:
            title = u'%s (%s)' % (cmd.title(), cmd.shortcut)
        else:
            title = cmd.title()
        btn = QtGui.QPushButton(title, focusPolicy=QtCore.Qt.NoFocus)
        btn.setToolTip(cmd.desc)
        return btn

    def _on_btn_pressed( self, cmd, *args ):
        print '* cmd_pane/command/run', repr(cmd.name), repr(cmd.desc), self.window, args
        self.window().run(cmd, *args)

    def __del__( self ):
        print '~cmd_pane'
