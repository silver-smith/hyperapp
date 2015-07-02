import weakref
from PySide import QtCore, QtGui
from util import make_action
from view_command import ViewCommandBase, BoundViewCommand
#import key_binding
#import cmd_view


class MenuBar(object):

    def __init__( self, app, window ):
        self.app = app
        self.window = window  # weakref.ref
        self.current_dir = None
        self.selected_elts = []
        self._build()

    def _build( self ):
        self.file_menu = self._build_global_menu('&File')
        self.dir_menu = QtGui.QMenu('&Dir')
        self.window_menu = QtGui.QMenu('W&indow')
        self.help_menu = QtGui.QMenu('H&elp')
        self.add_action_to_menu(self.help_menu, '&Dir commands', 'F1', MenuBar._open_dir_commands, weakref.ref(self))
        self.add_action_to_menu(self.help_menu, '&Current element commands', '.', MenuBar._open_elt_commands, weakref.ref(self))
        ## self.help_menu.setEnabled(False)
        menu_bar = self.window().menuBar()
        menu_bar.addMenu(self.file_menu)
        menu_bar.addMenu(self.dir_menu)
        menu_bar.addMenu(self.window_menu)
        menu_bar.addMenu(self.help_menu)

    def add_action_to_menu( self, menu, text, shortcut, fn, self_wr ):
        menu.addAction(make_action(menu, text, shortcut, fn, self_wr))

    def add_cmd_action_to_menu( self, menu, cmd, *args ):
        return
        menu.addAction(cmd.make_action(menu, *args))

    def _build_global_menu( self, title ):
        menu = QtGui.QMenu(title)
        window = self.window()
        for cmd in self.window().get_global_commands():
            assert isinstance(cmd, ViewCommandBase), repr(cmd)
            menu.addAction(cmd.make_action(menu, window))
        return menu

    def _current_view( self ):
        return self.window().get_current_view()

    @staticmethod
    def _open_dir_commands( self_wr ):
        self = self_wr()
        if self.current_dir is None: return
        self._current_view().open(cmd_view.Handle(None, [self.current_dir], take_dir_commands=True))

    @staticmethod
    def _open_elt_commands( self_wr ):
        self = self_wr()
        if not self.selected_elts: return
        self._current_view().open(cmd_view.Handle(None, [self.selected_elts], take_dir_commands=False))

    def view_changed( self, window ):
        self.current_dir = dir = window.get_object()
        self.help_menu.setEnabled(dir is not None)
        self._update_dir_menu(window)
        self._update_window_menu(window)

    def _update_dir_menu( self, window ):
        self.dir_menu.clear()
        view, commands = window.get_object_commands()
        for cmd in commands:
            self.add_cmd_action_to_menu(self.dir_menu, cmd, view)
        self.dir_menu.setEnabled(commands != [])

    def _update_window_menu( self, window ):
        self.window_menu.clear()
        # remove duplicate shortcuts, with latter (from deeper views) commands overriding former ones
        commands = []  # in reversed order
        shortcuts = set()
        for cmd in reversed(window.get_commands()):
            if not cmd.is_enabled():
                commands.append(cmd)
                continue
            cmd_shortcuts = set(cmd.get_shortcut_list())
            dups = shortcuts & cmd_shortcuts
            if dups:
                cmd = cmd.clone_without_shortcuts(dups)
            commands.append(cmd)
            shortcuts |= cmd_shortcuts
        last_view = None
        for cmd in reversed(commands):
            if last_view is not None and cmd.get_inst() is not last_view:
                self.window_menu.addSeparator()
            assert isinstance(cmd, BoundViewCommand), repr(cmd)
            self.window_menu.addAction(cmd.make_action(self.window_menu))
            last_view = cmd.get_inst()

    def selected_elements_changed( self, elts ):
        return
        self.selected_elts = elts

    def __del__( self ):
        print '~menu_bar'
