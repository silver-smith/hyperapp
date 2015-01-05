import weakref
from PySide import QtCore, QtGui
from util import make_action
#import key_binding
#import cmd_view


class MenuBar(object):

    def __init__( self, window ):
        self.window = window  # weakref.ref
        self.current_dir = None
        self.selected_elts = []
        self._build()

    def _build( self ):
        self.file_menu = self._build_global_menu('&File')
        self.dir_menu = QtGui.QMenu('&Dir')
        self.window_menu = QtGui.QMenu('W&indow')
        self.help_menu = QtGui.QMenu('H&elp')
        self.help_menu.addAction(make_action(self.window(), '&Dir commands', 'F1', self._open_dir_commands))
        self.help_menu.addAction(make_action(self.window(), '&Current element commands', '.', self._open_elt_commands))
        self.help_menu.setEnabled(False)
        menu_bar = self.window().menuBar()
        menu_bar.addMenu(self.file_menu)
        menu_bar.addMenu(self.dir_menu)
        menu_bar.addMenu(self.window_menu)
        menu_bar.addMenu(self.help_menu)

    def _build_global_menu( self, title ):
        menu = QtGui.QMenu(title)
        for cmd in self.window().get_global_commands():
            menu.addAction(cmd.make_action(self.window()))
        return menu

    def _current_view( self ):
        return self.window().current_view()

    def _open_dir_commands( self ):
        if self.current_dir is None: return
        self._current_view().open(cmd_view.Handle(None, [self.current_dir], take_dir_commands=True))

    def _open_elt_commands( self ):
        if not self.selected_elts: return
        self._current_view().open(cmd_view.Handle(None, [self.selected_elts], take_dir_commands=False))

    def view_changed( self, window ):
        self.current_dir = dir = window.current_dir()
        self.help_menu.setEnabled(dir is not None)
        self.dir_menu.clear()
        view = window.current_view()
        if dir is not None:
            commands = dir.get_dir_commands()
            for cmd in commands:
                self.dir_menu.addAction(cmd.make_action(self.window(), view, dir))
            self.dir_menu.setEnabled(commands != [])
        else:
            self.dir_menu.setEnabled(False)
        self._update_window_menu(window)

    def _update_window_menu( self, window ):
        self.window_menu.clear()
        last_view = None
        for cmd in window.get_commands():
            if last_view is not None and cmd.get_inst() is not last_view:
                self.window_menu.addSeparator()
            self.window_menu.addAction(cmd.make_action(self.window()))
            last_view = cmd.get_inst()

    def selected_elements_changed( self, elts ):
        self.selected_elts = elts
