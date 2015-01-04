# panel with commands for current dir and selected elements

import weakref
from PySide import QtCore, QtGui


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
        self._update_elts(window.current_view(), window.selected_elts())

    def selected_elements_changed( self, elts ):
        self._update_elts(self.window().current_view(), elts)

    def _update_dir( self, dir ):
        for btn in self.dir_buttons:
            btn.deleteLater()
        self.dir_buttons = []
        if dir is None: return
        view = self.window().current_view()
        idx = 0
        for cmd in dir.get_dir_commands():
                button = self._make_button(cmd)
                button.pressed.connect(lambda cmd=cmd: cmd.run_dir_command(dir, view))
                self.layout.insertWidget(idx, button)  # must be inserted before spacing
                self.dir_buttons.append(button)
                idx += 1

    def _update_elts( self, view, elts ):
        for btn in self.elts_buttons:
            btn.deleteLater()
        self.elts_buttons = []
        if not elts: return
        dir = self.current_dir
        ## for cmd in collect_objs_commands(elts):
        ##     if not cmd.enabled: continue
        ##     btn = self._make_btn(cmd)
        ##     args = cmd_elements_to_args(cmd, elts)
        ##     btn.pressed.connect(lambda cmd=cmd, args=args: self._run_element_command(cmd, view, dir, *args))
        ##     self.layout.addWidget(btn)
        ##     self.elts_buttons.append(btn)

    def _make_button( self, cmd ):
        if cmd.shortcut:
            text = u'%s (%s)' % (cmd.text, cmd.shortcut)
        else:
            text = cmd.text
        button = QtGui.QPushButton(text, focusPolicy=QtCore.Qt.NoFocus)
        button.setToolTip(cmd.desc)
        return button

    def _run_dir_command( self, cmd, view ):
        print '* cmd_pane/_run_dir_command', cmd.id, view
        view.run_dir_command(cmd.id)

    # multi-select not yet supported
    def _run_element_command( self, cmd, view, dir, elt ):
        print '* cmd_pane/_run_element_command', cmd.id, view, dir, elt
        element_key = dir.element2key(elt)
        view.run_element_command(cmd.id, element_key)

    def __del__( self ):
        print '~cmd_pane'
