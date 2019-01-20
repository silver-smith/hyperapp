import logging
import weakref
from PySide import QtCore, QtGui
from .util import make_action, make_async_action
from .command import Command, WindowCommand

log = logging.getLogger(__name__)


class MenuBar(object):

    def __init__(self, app, window, locale, module_command_registry, resources_manager):
        self.app = app
        self.window = window  # weakref.ref
        self._locale = locale
        self._module_command_registry = module_command_registry
        self._resources_manager = resources_manager
        self.current_dir = None
        self._build()

    def _build(self):
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

    def add_action_to_menu(self, menu, text, shortcuts, fn, self_wr):
        menu.addAction(make_action(menu, text, shortcuts, fn, self_wr))

    def _build_global_menu(self, title):
        menu = QtGui.QMenu(title)
        window = self.window()
        for cmd in self._module_command_registry.get_all_commands():
            assert isinstance(cmd, Command), repr(cmd)
            window_command = WindowCommand.from_command(cmd, window)
            menu.addAction(self._make_action(menu, window_command))
        if not menu.isEmpty():
            menu.addSeparator()
        for cmd in self.window().get_global_commands():
            assert isinstance(cmd, Command), repr(cmd)
            menu.addAction(self._make_action(menu, cmd))
        return menu

    def _current_view(self):
        return self.window().get_current_view()

    @staticmethod
    def _open_dir_commands(self_wr):
        self = self_wr()
        if self.current_dir is None: return
        assert 0  # todo
        ## self._current_view().open(cmd_view.Handle(None, [self.current_dir], take_dir_commands=True))

    @staticmethod
    def _open_elt_commands(self_wr):
        self = self_wr()
        assert 0  # todo
        ## self._current_view().open(cmd_view.Handle(None, [self.selected_elts], take_dir_commands=False))

    def view_changed(self, window):
        log.debug('-- menu_bar view_changed object=%r', window.get_object())
        self.current_dir = dir = window.get_object()
        self.help_menu.setEnabled(dir is not None)
        used_shortcuts = set()
        self._update_dir_menu(window, used_shortcuts)
        self._update_window_menu(window, used_shortcuts)

    def view_commands_changed(self, window, command_kinds):
        pass
        
    def _make_action(self, menu, cmd, used_shortcuts=None):
        resource = self._resources_manager.resolve(cmd.resource_id + [self._locale])
        if resource:
            text = resource.text
            shortcuts = resource.shortcuts
        else:
            text = '%s/%s' % (cmd.resource_id, cmd.id)
            shortcuts = None
        if not cmd.is_enabled():
            shortcuts = None
        if used_shortcuts is not None:
            # remove duplicates
            shortcuts = [sc for sc in shortcuts or [] if sc not in used_shortcuts]
            used_shortcuts |= set(shortcuts)
        action = make_async_action(menu, text, shortcuts, cmd.run)
        action.setEnabled(cmd.is_enabled())
        return action

    def _update_dir_menu(self, window, used_shortcuts):
        self.dir_menu.clear()
        command_list = window.get_command_list()
        for command in command_list:
            assert isinstance(command, Command), repr(command)
            if command.kind != 'object': continue
            #if command.is_system(): continue
            self.dir_menu.addAction(self._make_action(self.dir_menu, command, used_shortcuts))
        self.dir_menu.setEnabled(command_list != [])

    def _update_window_menu(self, window, used_shortcuts):
        self.window_menu.clear()
        # later commands are from deeper views
        # we must iterate in reverse order so deeper view's shortcuts override shallow ones
        last_view = None
        last_action = None
        for command in reversed(window.get_command_list()):
            assert isinstance(command, Command), repr(command)
            if command.kind != 'view': continue
            #if command.is_system(): continue
            action = self._make_action(self.window_menu, command, used_shortcuts)
            if last_action:
                self.window_menu.insertAction(last_action, action)
            else:
                self.window_menu.addAction(action)
            if last_view and command.get_view() is not last_view:
                self.window_menu.insertSeparator(last_action)
            last_action = action
            last_view = command.get_view()

    def __del__(self):
        log.info('~menu_bar')
