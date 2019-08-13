import asyncio
import logging
from functools import partial

from PySide import QtCore, QtGui

from hyperapp.common.htypes import resource_key_t
from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.ref import ref_repr
from hyperapp.client.util import make_async_action
from hyperapp.client.module import ClientModule
from . import htypes
from .text_object import TextObject
from .tab_view import TabView
from .window import Window

_log = logging.getLogger(__name__)


class _CurrentItemObserver:

    def __init__(self, layout_manager, object):
        self._layout_manager = layout_manager
        self._object = object

    def current_changed(self, current_item_key):
        self._layout_manager.update_element_commands(self._object, current_item_key)


class History:

    def __init__(self):
        self._backward = []
        self._forward = []

    def add_new(self, state):
        self._backward.append(state)
        self._forward.clear()

    def pop_back(self, current_state):
        if not self._backward:
            return None
        if current_state is not None:
            self._forward.append(current_state)
        return self._backward.pop(-1)

    def pop_forward(self, current_state):
        if not self._forward:
            return None
        if current_state is not None:
            self._backward.append(current_state)
        return self._forward.pop(-1)


class LayoutManager:

    def __init__(self, type_resolver, resource_resolver, module_command_registry, object_registry, view_producer):
        self._type_resolver = type_resolver
        self._resource_resolver = resource_resolver
        self._module_command_registry = module_command_registry
        self._object_registry = object_registry
        self._view_producer = view_producer
        self._locale = 'en'
        self._cmd_pane = self._construct_cmd_pane()
        self._dir_buttons = []
        self._element_buttons = []
        self._current_state = None
        self._current_item_observer = None
        self._history = History()

    async def build_default_layout(self, app):
        self._current_state = state = htypes.text.text("Welcome to hyperapp")
        text_object = self._object_registry.resolve(state)
        text_view = await self._view_producer.produce_view(state, text_object)
        self._tab_view = tab_view = TabView()
        tab_view.addTab(text_view, text_view.get_title())
        window = Window(on_closed=app.stop)
        window.setCentralWidget(tab_view)
        window.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._cmd_pane)
        # window.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._cmd_pane)
        window.menuBar().addMenu(self._build_global_menu(app, "&File"))
        window.menuBar().addMenu(self._build_navigation_menu("&Navigation"))
        window.show()
        self._window = window

    def _build_global_menu(self, app, title):
        menu = QtGui.QMenu(title)
        for command in self._module_command_registry.get_all_commands():
            resource = self._resource_resolver.resolve(command.resource_key, self._locale)
            if resource:
                text = resource.text
                shortcut_list = resource.shortcut_list
            else:
                text = command.id
                shortcut_list = None
            menu.addAction(make_async_action(menu, text, shortcut_list, self._run_command, command))
        if not menu.isEmpty():
            menu.addSeparator()
        for command in app.get_global_commands():
            menu.addAction(make_async_action(menu, command.id, [], self._run_command, command))
        return menu

    def _build_navigation_menu(self, title):
        menu = QtGui.QMenu(title)
        menu.addAction(make_async_action(menu, 'Go back', ['Escape', 'Alt+Left'], self._navigate_backward))
        menu.addAction(make_async_action(menu, 'Go forward', ['Alt+Right'], self._navigate_forward))
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

    async def _run_command(self, command, *args, **kw):
        _log.info('Run command: %r', command.id)
        state = await command.run(*args, **kw)
        if state is None:
            return
        await self.open(state)

    async def open(self, rec):
        if self._current_state:
            self._history.add_new(self._current_state)
        await self._open(rec)

    async def _open(self, state):
        object = await self._object_registry.resolve_async(state)
        self._current_item_observer = observer = _CurrentItemObserver(self, object)
        view = await self._view_producer.produce_view(state, object, observer)
        tab_view = self._tab_view
        old_widget = tab_view.widget(0)
        tab_view.removeTab(0)
        old_widget.deleteLater()
        tab_view.insertTab(0, view, view.get_title())
        view.setFocus()
        self._current_state = state
        self._clean_element_commands()
        self._update_dir_buttons(object)

    def _update_dir_buttons(self, object):
        for button in self._dir_buttons:
            button.deleteLater()
        self._dir_buttons.clear()
        for command in object.get_command_list():
            if command.kind != 'object':
                continue
            button = self._make_button_for_current_object(command)
            button.pressed.connect(partial(asyncio.ensure_future, self._run_command(command)))
            layout = self._cmd_pane.widget().layout()
            layout.insertWidget(len(self._dir_buttons), button)  # must be inserted before spacing
            self._dir_buttons.append(button)

    def update_element_commands(self, object, current_item_key):
        _log.debug('Update element commands for item %r', current_item_key)
        self._clean_element_commands()
        for command in object.get_item_command_list(current_item_key):
            button = self._make_button_for_current_object(command)
            button.pressed.connect(partial(asyncio.ensure_future, self._run_command(command, current_item_key)))
            layout = self._cmd_pane.widget().layout()
            layout.addWidget(button)
            self._element_buttons.append(button)

    def _clean_element_commands(self):
        for button in self._element_buttons:
            button.deleteLater()
        self._element_buttons.clear()

    def _state_type_ref(self, state):
        current_t = deduce_value_type(state)
        return self._type_resolver.reverse_resolve(current_t)

    def _make_button_for_current_object(self, command):
        type_ref = self._state_type_ref(self._current_state)
        resource_key = resource_key_t(type_ref, command.resource_key.path[1:])  # skip class name
        resource = self._resource_resolver.resolve(resource_key, self._locale)
        if resource:
            text = resource.text
            shortcut_list = resource.shortcut_list
            if resource.is_default:
                shortcut_list = ['Return', *shortcut_list]
            if shortcut_list:
                text = '%s (%s)' % (text, shortcut_list[0])
            description = resource.description
        else:
            text = command.id
            shortcut_list = None
            description = '.'.join(resource_key.path)
        button = QtGui.QPushButton(text, focusPolicy=QtCore.Qt.NoFocus)
        if shortcut_list:
            button.setShortcut(shortcut_list[0])
        button.setToolTip(description)
        return button

    async def _navigate_backward(self):
        state = self._history.pop_back(self._current_state)
        if state is not None:
            await self._open(state)

    async def _navigate_forward(self):
        state = self._history.pop_forward(self._current_state)
        if state is not None:
            await self._open(state)


class ViewOpener:

    def __init__(self, layout_manager):
        self._layout_manager = layout_manager

    async def open_rec(self, rec):
        await self._layout_manager.open(rec)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.layout_manager = layout_manager = LayoutManager(
            services.type_resolver,
            services.resource_resolver,
            services.module_command_registry,
            services.object_registry,
            services.view_producer,
            )
        services.view_opener = ViewOpener(layout_manager)
