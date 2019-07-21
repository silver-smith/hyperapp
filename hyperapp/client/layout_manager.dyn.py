from PySide import QtCore, QtGui

from hyperapp.common.htypes import resource_key_t
from hyperapp.client.util import make_async_action
from hyperapp.client.module import ClientModule
from .text_object import TextObject
from .text_view import TextView
from .tab_view import TabView
from .window import Window
from .list_object import ListObject
from .list_view import ListView


MODULE_NAME = 'layout_manager'


class LayoutManager(object):

    def __init__(self, resource_resolver, module_command_registry, objimpl_registry):
        self._resource_resolver = resource_resolver
        self._module_command_registry = module_command_registry
        self._objimpl_registry = objimpl_registry

    def build_default_layout(self, app):
        text_object = TextObject('hello')
        text_view = TextView(text_object)
        self._tab_view = tab_view = TabView()
        tab_view.addTab(text_view, text_view.get_title())
        window = Window(on_closed=app.stop)
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

    async def _run_global_command(self, command):
        state = await command.run()
        object = await self._objimpl_registry.resolve_async(state)
        assert isinstance(object, ListObject), repr(object)
        locale = 'en'
        sort_column_id = 'key'
        resource_key = resource_key_t(__module_ref__, [])
        list_view = ListView(self._resource_resolver, locale, resource_key, object)
        tab_view = self._tab_view
        old_widget = tab_view.widget(0)
        tab_view.removeTab(0)
        old_widget.deleteLater()
        tab_view.insertTab(0, list_view, list_view.get_title())


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.layout_manager = LayoutManager(
            services.resource_resolver,
            services.module_command_registry,
            services.objimpl_registry,
            )
