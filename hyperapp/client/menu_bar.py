import logging
import weakref
from PySide import QtCore, QtGui
from .util import make_action, make_async_action
from .command import Command, WindowCommand
from .module import Module

log = logging.getLogger(__name__)


class MenuBar(object):

    def __init__( self, app, window, locale, resources_registry ):
        self.app = app
        self.window = window  # weakref.ref
        self._locale = locale
        self._resources_registry = resources_registry
        self.current_dir = None
        self._build()

    def _build( self ):
        self.file_menu = self._build_global_menu('&File')
        self.dir_menu = QtGui.QMenu('&Dir')
        self.window_menu = QtGui.QMenu('&Window')
        self.help_menu = QtGui.QMenu('H&elp')
        self.add_action_to_menu(self.help_menu, '&Dir commands', ['F1'], MenuBar._open_dir_commands, weakref.ref(self))
        self.add_action_to_menu(self.help_menu, '&Current element commands', ['.'], MenuBar._open_elt_commands, weakref.ref(self))
        ## self.help_menu.setEnabled(False)
        menu_bar = self.window().menuBar()
        menu_bar.addMenu(self.file_menu)
        menu_bar.addMenu(self.dir_menu)
        menu_bar.addMenu(self.window_menu)
        menu_bar.addMenu(self.help_menu)

    def add_action_to_menu( self, menu, text, shortcuts, fn, self_wr ):
        menu.addAction(make_action(menu, text, shortcuts, fn, self_wr))

    def _build_global_menu( self, title ):
        menu = QtGui.QMenu(title)
        window = self.window()
        for cmd in Module.get_all_commands():
            assert isinstance(cmd, Command), repr(cmd)
            window_command = WindowCommand.from_command(cmd, window)
            menu.addAction(self._make_action(menu, window_command))
        if not menu.isEmpty():
            menu.addSeparator()
        for cmd in self.window().get_global_commands():
            assert isinstance(cmd, Command), repr(cmd)
            menu.addAction(self._make_action(menu, cmd))
        return menu

    def _current_view( self ):
        return self.window().get_current_view()

    @staticmethod
    def _open_dir_commands( self_wr ):
        self = self_wr()
        if self.current_dir is None: return
        assert 0  # todo
        ## self._current_view().open(cmd_view.Handle(None, [self.current_dir], take_dir_commands=True))

    @staticmethod
    def _open_elt_commands( self_wr ):
        self = self_wr()
        assert 0  # todo
        ## self._current_view().open(cmd_view.Handle(None, [self.selected_elts], take_dir_commands=False))

    def view_changed( self, window ):
        self.current_dir = dir = window.get_object()
        self.help_menu.setEnabled(dir is not None)
        self._update_dir_menu(window)
        self._update_window_menu(window)

    def view_commands_changed( self, window, command_kinds ):
        pass
        
    def _make_action( self, menu, cmd ):
        resources = self._resources_registry.resolve(cmd.resource_id, self._locale)
        if not resources:
            return make_async_action(menu, '%s/%s' % (cmd.resource_id, cmd.id), None, cmd.run)
        for res in resources.commands:
            if res.id == cmd.id:
                break
        else:
            print([rc.id for rc in resources.commands])
            assert False, 'Resource %r does not contain command %r' % (cmd.resource_id, cmd.id)
        return make_async_action(menu, res.text, res.shortcuts, cmd.run)

    def _update_dir_menu( self, window ):
        self.dir_menu.clear()
        commands = window.get_commands()
        for cmd in commands:
            assert isinstance(cmd, Command), repr(cmd)
            if cmd.kind != 'object': continue
            #if cmd.is_system(): continue
            self.dir_menu.addAction(self._make_action(self.dir_menu, cmd))
        self.dir_menu.setEnabled(commands != [])

    def _update_window_menu( self, window ):
        self.window_menu.clear()
        # remove duplicate shortcuts, with latter (from deeper views) commands overriding former ones
        commands = []  # in reversed order
        shortcuts = set()
        for cmd in reversed(window.get_commands()):
            assert isinstance(cmd, Command), repr(cmd)
            if cmd.kind != 'view': continue
            #if cmd.is_system(): continue
            if not cmd.is_enabled():
                commands.append(cmd)
                continue
            #cmd_shortcuts = set(cmd.get_shortcut_list())
            cmd_shortcuts = set()
            dups = shortcuts & cmd_shortcuts
            if dups:
                cmd = cmd.clone_without_shortcuts(dups)
            commands.append(cmd)
            shortcuts |= cmd_shortcuts
        last_view = None
        for cmd in reversed(commands):
            if last_view is not None and cmd.get_view() is not last_view:
                self.window_menu.addSeparator()
            self.window_menu.addAction(self._make_action(self.window_menu, cmd))
            last_view = cmd.get_view()

    def __del__( self ):
        log.info('~menu_bar')
