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
from .layout_registry import LayoutViewProducer
from .text_object import TextObject
from .tab_view import TabView
from .window import Window

_log = logging.getLogger(__name__)

LOCALE = 'en'


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

    def add_new(self, piece):
        self._backward.append(piece)
        self._forward.clear()

    def pop_back(self, current_piece):
        if not self._backward:
            return None
        if current_piece is not None:
            self._forward.append(current_piece)
        return self._backward.pop(-1)

    def pop_forward(self, current_piece):
        if not self._forward:
            return None
        if current_piece is not None:
            self._backward.append(current_piece)
        return self._forward.pop(-1)


class LayoutManager:

    def __init__(
            self,
            ref_resolver,
            type_resolver,
            resource_resolver,
            module_command_registry,
            object_registry,
            view_producer_registry,
            layout_registry,
            layout_resolver,
            ):
        self._ref_resolver = ref_resolver
        self._type_resolver = type_resolver
        self._resource_resolver = resource_resolver
        self._module_command_registry = module_command_registry
        self._object_registry = object_registry
        self._view_producer_registry = view_producer_registry
        self._layout_registry = layout_registry
        self._layout_resolver = layout_resolver
        self._locale = 'en'
        self._cmd_pane = self._construct_cmd_pane()
        self._dir_buttons = []
        self._element_buttons = []
        self._current_piece = None
        self._current_item_observer = None
        self._history = History()

    async def build_default_layout(self, app):
        self._current_piece = piece = htypes.text.text("Welcome to hyperapp")
        text_object = self._object_registry.resolve(piece)
        text_view = await self.produce_view(piece, text_object)
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
        _log.info('Run command %r', command.id)
        piece = await command.run(*args, **kw)
        if piece is None:
            return
        await self.open(piece)

    async def _run_command_with_layout(self, command_id, layout, *args, **kw):
        _log.info('Run command %r with layout %r', command_id, layout)
        await self.open(self._current_piece, layout)

    async def open(self, piece, layout=None):
        if self._current_piece:
            self._history.add_new(self._current_piece)
        await self._open(piece, layout)

    async def _open(self, piece, layout=None):
        if not layout:
            layout = self._pick_piece_layout(piece)
        object = await self._object_registry.resolve_async(piece)
        self._current_item_observer = observer = _CurrentItemObserver(self, object)
        view = await self._produce_view(layout, piece, object, observer)
        self._set_current_view(view)
        self._current_piece = piece
        self._clean_element_commands()
        await self._update_dir_buttons(piece, object, layout)

    def _set_current_view(self, view):
        tab_view = self._tab_view
        old_view = tab_view.widget(0)
        tab_view.removeTab(0)
        old_view.deleteLater()
        tab_view.insertTab(0, view, view.get_title())
        view.setFocus()

    # returns None if none registered
    def _pick_piece_layout(self, piece):
        type_ref = self._piece_type_ref(piece)
        resource_key = resource_key_t(type_ref, ['layout'])
        return self._resource_resolver.resolve(resource_key, LOCALE)

    async def _produce_view(self, layout, piece, object, observer=None):
        if layout and layout.view_ref:
            view_producer = await self._layout_resolver.resolve(layout.view_ref)
            _log.info("Producing view for %r with %s %s using %s", piece, ref_repr(layout.view_ref), layout, view_producer)
        else:
            view_producer = self
            _log.info("Producing view for %r using default producer", piece)
        return (await view_producer.produce_view(piece, object, observer))

    async def pick_layout_and_produce_view(self, piece, object, observer=None):
        layout = self._pick_piece_layout(piece)
        return (await self._produce_view(layout, piece, object, observer))

    async def produce_view(self, piece, object, observer=None):
        return (await self._view_producer_registry.produce_view(piece, object, observer))

    async def _update_dir_buttons(self, piece, object, layout):
        for button in self._dir_buttons:
            button.deleteLater()
        self._dir_buttons.clear()
        for command in object.get_command_list():
            if command.kind != 'object':
                continue
            button = self._make_button_for_current_object_command(command)
            button.pressed.connect(partial(asyncio.ensure_future, self._run_command(command)))
            qt_layout = self._cmd_pane.widget().layout()
            qt_layout.insertWidget(len(self._dir_buttons), button)  # must be inserted before spacing
            self._dir_buttons.append(button)
        if not layout:
            return
        for command in layout.layout_commands:
            if command.layout_ref:
                layout = await self._ref_resolver.resolve_ref_to_object(command.layout_ref)
            else:
                layout = None
            resource_path = ['command', command.command_id]
            button = self._make_button_for_current_object(command.command_id, resource_path)
            button.pressed.connect(partial(asyncio.ensure_future, self._run_command_with_layout(command.command_id, layout)))
            qt_layout = self._cmd_pane.widget().layout()
            qt_layout.insertWidget(len(self._dir_buttons), button)  # must be inserted before spacing
            self._dir_buttons.append(button)

    def update_element_commands(self, object, current_item_key):
        _log.debug('Update element commands for item %r', current_item_key)
        self._clean_element_commands()
        for command in object.get_item_command_list(current_item_key):
            button = self._make_button_for_current_object_command(command)
            button.pressed.connect(partial(asyncio.ensure_future, self._run_command(command, current_item_key)))
            layout = self._cmd_pane.widget().layout()
            layout.addWidget(button)
            self._element_buttons.append(button)

    def _clean_element_commands(self):
        for button in self._element_buttons:
            button.deleteLater()
        self._element_buttons.clear()

    def _piece_type_ref(self, piece):
        t = deduce_value_type(piece)
        return self._type_resolver.reverse_resolve(t)

    def _make_button_for_current_object_command(self, command):
        resource_path = command.resource_key.path[1:]  # skip class name
        return self._make_button_for_current_object(command.id, resource_path)

    def _make_button_for_current_object(self, command_id, resource_path):
        type_ref = self._piece_type_ref(self._current_piece)
        resource_key = resource_key_t(type_ref, resource_path)
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
            text = command_id
            shortcut_list = None
            description = '.'.join(resource_key.path)
        button = QtGui.QPushButton(text, focusPolicy=QtCore.Qt.NoFocus)
        if shortcut_list:
            button.setShortcut(shortcut_list[0])
        button.setToolTip(description)
        return button

    async def _navigate_backward(self):
        piece = self._history.pop_back(self._current_piece)
        if piece is not None:
            await self._open(piece)

    async def _navigate_forward(self):
        piece = self._history.pop_forward(self._current_piece)
        if piece is not None:
            await self._open(piece)


class ViewProducer(LayoutViewProducer):

    def __init__(self, layout_manager):
        self._layout_manager = layout_manager

    async def produce_view(self, piece, object, observer=None):
        return (await self._layout_manager.pick_layout_and_produce_view(piece, object, observer))

    async def produce_default_view(self, piece, object, observer=None):
        return (await self._layout_manager.produce_view(piece, object, observer))


class ViewOpener:

    def __init__(self, layout_manager):
        self._layout_manager = layout_manager

    async def open_rec(self, rec):
        await self._layout_manager.open(rec)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.layout_manager = layout_manager = LayoutManager(
            services.async_ref_resolver,
            services.type_resolver,
            services.resource_resolver,
            services.module_command_registry,
            services.object_registry,
            services.view_producer_registry,
            services.layout_registry,
            services.layout_resolver,
            )
        services.view_producer = ViewProducer(layout_manager)
        services.view_opener = ViewOpener(layout_manager)
