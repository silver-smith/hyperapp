import asyncio
import logging
from functools import partial

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

_log = logging.getLogger(__name__)

MODULE_NAME = 'layout_manager'


class LayoutManager(object):

    def __init__(self, resource_resolver, module_command_registry, objimpl_registry):
        self._resource_resolver = resource_resolver
        self._module_command_registry = module_command_registry
        self._objimpl_registry = objimpl_registry
        self._cmd_pane = self._construct_cmd_pane()
        self._dir_buttons = []

    def build_default_layout(self, app):
        text_object = TextObject('hello')
        text_view = TextView(text_object)
        self._tab_view = tab_view = TabView()
        tab_view.addTab(text_view, text_view.get_title())
        window = Window(on_closed=app.stop)
        window.setCentralWidget(tab_view)
        window.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._cmd_pane)
        # window.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._cmd_pane)
        window.menuBar().addMenu(self._build_global_menu(app, window, "&File"))
        window.show()
        self._window = window

    def _build_global_menu(self, app, window, title):
        menu = QtGui.QMenu(title)
        for command in self._module_command_registry.get_all_commands():
            menu.addAction(make_async_action(menu, command.id, [], self._run_command, command))
        if not menu.isEmpty():
            menu.addSeparator()
        for command in app.get_global_commands():
            menu.addAction(make_async_action(menu, command.id, [], self._run_command, command))
        return menu

    def _construct_cmd_pane(self):
        layout = QtGui.QVBoxLayout(spacing=1)
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addSpacing(10)
        widget = QtGui.QWidget()
        widget.setLayout(layout)
        pane = QtGui.QDockWidget()
        pane.setWidget(widget)
        pane.setFeatures(pane.NoDockWidgetFeatures)
        return pane

    def _update_dir_buttons(self, object):
        for button in self._dir_buttons:
            button.deleteLater()
        self._dir_buttons.clear()
        for command in object.get_command_list():
            if command.kind != 'object':
                continue
            text = command.id
            button = QtGui.QPushButton(text, focusPolicy=QtCore.Qt.NoFocus)
            button.pressed.connect(partial(asyncio.ensure_future, self._run_command(command)))
            self._cmd_pane.widget().layout().addWidget(button)
            self._dir_buttons.append(button)

    async def _run_command(self, command):
        _log.info('Run command: %r', command.id)
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
        self._update_dir_buttons(object)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.layout_manager = LayoutManager(
            services.resource_resolver,
            services.module_command_registry,
            services.objimpl_registry,
            )
