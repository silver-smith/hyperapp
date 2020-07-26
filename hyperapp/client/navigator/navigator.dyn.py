# navigator component - container keeping navigation history and allowing go backward and forward

import logging
from collections import namedtuple
from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .view import View
from .layout import RootVisualItem, VisualItem, GlobalLayout

_log = logging.getLogger(__name__)


_HistoryItem = namedtuple('_HistoryItem', 'object layout')


class _History:

    def __init__(self):
        self._backward_piece_list = []  # last element is current piece
        self._forward_piece_list = []

    @property
    def current_piece(self):
        return self._backward_piece_list[-1]

    def append(self, piece):
        self._backward_piece_list.append(piece)
        self._forward_piece_list.clear()

    def move_backward(self):
        # Move current piece to forward list and return previous one
        current_piece = self._backward_piece_list.pop()
        self._forward_piece_list.append(current_piece)
        return self._backward_piece_list[-1]

    def move_forward(self):
        piece = self._forward_piece_list.pop()
        self._backward_piece_list.append(piece)
        return piece


class NavigatorLayout(GlobalLayout):

    @classmethod
    async def from_data(cls,
                        state, path, command_hub, view_opener,
                        ref_registry, async_ref_resolver, type_resolver,
                        object_registry, object_layout_resolver, object_layout_producer, module_command_registry, params_editor):
        self = cls(ref_registry, async_ref_resolver, type_resolver,
                   object_registry, object_layout_resolver, object_layout_producer, module_command_registry, params_editor,
                   path, command_hub, view_opener)
        await self._async_init(state.current_piece_ref, state.current_layout_ref)
        return self

    def __init__(self, ref_registry, async_ref_resolver, type_resolver,
                 object_registry, object_layout_resolver, object_layout_producer, module_command_registry, params_editor,
                 path, command_hub, view_opener):
        super().__init__(path)
        self._ref_registry = ref_registry
        self._async_ref_resolver = async_ref_resolver
        self._type_resolver = type_resolver
        self._object_registry = object_registry
        self._object_layout_resolver = object_layout_resolver
        self._object_layout_producer = object_layout_producer
        self._module_command_registry = module_command_registry
        self._params_editor = params_editor
        self._command_hub = command_hub
        self._view_opener = view_opener
        self._history = _History()
        self._current_object = None
        self._current_layout = None
        self._current_view = None

    async def _async_init(self, initial_piece_ref, initial_layout_ref):
        piece = await self._async_ref_resolver.resolve_ref_to_object(initial_piece_ref)
        self._current_object = object = await self._object_registry.resolve_async(piece)
        if initial_layout_ref:
            self._current_layout = await self._object_layout_resolver.resolve(initial_layout_ref, object)
        else:
            self._current_layout = await self._object_layout_producer.produce_layout(object)
        self._history.append(_HistoryItem(object, self._current_layout))

    @property
    def data(self):
        current_piece_ref = self._ref_registry.register_object(self._current_object.data)
        current_layout_ref = self._ref_registry.register_object(self._current_layout.data)
        return htypes.navigator.navigator(current_piece_ref, current_layout_ref)

    async def create_view(self):
        self._current_view = await self._current_layout.create_view(self._command_hub)
        return self._current_view

    async def visual_item(self):
        piece = self._current_object.data
        return RootVisualItem('Navigator', children=[
            VisualItem(0, 'current', str(piece)),
            ])

    def get_current_commands(self):
        return [
            *super().get_current_commands(),
            *self._get_global_commands(),
            *self._get_current_layout_commands(),
            ]

    def _get_global_commands(self):
        for command in self._module_command_registry.get_all_commands():
            yield (command
                   .with_(wrapper=self._open_layout)
                   )

    def _get_current_layout_commands(self):
        for command in self._current_layout.get_current_commands(self._current_view):
            yield (command
                   .with_(wrapper=self._open_layout)
                   )

    async def _open_layout(self, resolved_piece):
        await self._open_layout_impl(resolved_piece.object, resolved_piece.layout)
        self._history.append(_HistoryItem(resolved_piece.object, resolved_piece.layout))

    async def _open_piece(self, piece):
        await self._open_piece_impl(piece)
        # self._history.append(piece)  # todo

    async def _open_piece_impl(self, piece):
        object = await self._object_registry.resolve_async(piece)
        layout = await self._object_layout_producer.produce_layout(object)
        self._current_object = object
        await self._open_layout_impl(layout)

    async def _open_layout_impl(self, object, layout):
        view = await layout.create_view(self._command_hub)
        self._view_opener.open(view)
        self._current_object = object
        self._current_layout = layout
        self._current_view = view
        self._command_hub.update()

    @command('go_backward')
    async def _go_backward(self):
        try:
            item = self._history.move_backward()
        except IndexError:
            return
        await self._open_layout_impl(item.object, item.layout)

    @command('go_forward')
    async def _go_forward(self):
        try:
            item = self._history.move_forward()
        except IndexError:
            return
        await self._open_layout_impl(item.object, item.layout)

    @command('open_layout_editor')
    async def _open_layout_editor(self):
        current_piece_ref = self._ref_registry.register_object(self._current_object.data)
        piece = htypes.layout_key_list.layout_key_list(current_piece_ref)
        await self._open_piece(piece)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.view_registry.register_type(
            htypes.navigator.navigator,
            NavigatorLayout.from_data,
            services.ref_registry,
            services.async_ref_resolver,
            services.type_resolver,
            services.object_registry,
            services.object_layout_resolver,
            services.object_layout_producer,
            services.module_command_registry,
            services.params_editor,
            )
