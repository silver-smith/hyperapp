from PySide import QtCore, QtGui

from hyperapp.client.util import make_async_action
from hyperapp.client.module import ClientModule
from .text_object import TextObject
from .text_view import TextView
from .tab_view import TabView
from .window import Window


MODULE_NAME = 'layout_manager'


class LayoutManager(object):

    def __init__(self, module_command_registry):
        self._module_command_registry = module_command_registry

    def build_default_layout(self, app):
        text_object = TextObject('hello')
        text_view = TextView(text_object)
        tab_view = TabView()
        tab_view.addTab(text_view, text_view.get_title())
        window = Window()
        window.setCentralWidget(tab_view)
        # window.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._cmd_pane)
        window.menuBar().addMenu(self._build_global_menu(app, window, "&File"))
        window.show()
        self._window = window

    def _build_global_menu(self, app, window, title):
        menu = QtGui.QMenu(title)
        for command in self._module_command_registry.get_all_commands():
            menu.addAction(make_async_action(menu, command.id, [], self._run_global_command, command))
        if not menu.isEmpty():
            menu.addSeparator()
        for command in app.get_global_commands():
            menu.addAction(make_async_action(menu, command.id, [], self._run_global_command, command))
        return menu

    def _run_global_command(self, command):
        assert 0, command


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.layout_manager = LayoutManager(services.module_command_registry)
