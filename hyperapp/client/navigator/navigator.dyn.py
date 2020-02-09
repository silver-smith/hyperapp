# navigator component - container keeping navigation history and allowing go backward and forward

import logging
from functools import partial

from hyperapp.client.commander import FreeFnCommand
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .view import View
from .layout import RootVisualItem, VisualItem, Layout

_log = logging.getLogger(__name__)


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


class _CurrentItemObserver:

    def __init__(self, layout, piece, object):
        self._layout = layout
        self._piece = piece
        self._object = object

    def current_changed(self, current_item_key):
        self._layout._update_element_commands(self._piece, self._object, current_item_key)


class NavigatorLayout(Layout):

    @classmethod
    async def from_data(cls,
                        state, path, command_hub, view_opener,
                        ref_registry, object_registry, view_producer_registry, module_command_registry, async_ref_resolver, params_editor):
        self = cls(ref_registry, object_registry, view_producer_registry, module_command_registry, async_ref_resolver, params_editor,
                   path, command_hub, view_opener)
        await self._async_init(state.current_piece_ref)
        return self

    def __init__(self,
                 ref_registry, object_registry, view_producer_registry, module_command_registry, async_ref_resolver, params_editor,
                 path, command_hub, view_opener):
        super().__init__(path)
        self._ref_registry = ref_registry
        self._object_registry = object_registry
        self._view_producer_registry = view_producer_registry
        self._module_command_registry = module_command_registry
        self._async_ref_resolver = async_ref_resolver
        self._params_editor = params_editor
        self._command_hub = command_hub
        self._view_opener = view_opener
        self._history = _History()
        self._current_piece = None
        self._current_object = None
        self._current_layout = None

    async def _async_init(self, initial_piece_ref):
        self._initial_piece = piece = await self._async_ref_resolver.resolve_ref_to_object(initial_piece_ref)
        self._history.append(piece)

    def get_view_ref(self):
        current_piece_ref = self._ref_registry.register_object(self._current_piece)
        view = htypes.navigator.navigator(current_piece_ref)
        return self._ref_registry.register_object(view)

    async def create_view(self):
        self._current_piece = piece = self._initial_piece
        self._current_object = object = await self._object_registry.resolve_async(piece)
        layout = await self._view_producer_registry.produce_layout(piece, object, command_hub=None)
        self._current_layout = layout
        return (await layout.create_view())

    async def visual_item(self):
        piece = self._current_piece
        return RootVisualItem('Navigator', children=[
            VisualItem(0, 'current', str(piece)),
            ])

    def get_current_commands(self):
        piece = self._current_piece
        object = self._current_object
        return [
            *self._get_view_commands(),
            *self._get_global_commands(piece),
            *self._get_object_commands(piece, object),
            ]

    def _get_view_commands(self):
        yield self._go_backward
        yield self._go_forward

    def _get_global_commands(self, piece):
        for command in self._module_command_registry.get_all_commands():
            yield FreeFnCommand.from_command(command, partial(self._run_command, piece, command))

    def _get_object_commands(self, piece, object):
        for command in object.get_command_list():
            if command.kind != 'object':
                continue
            yield FreeFnCommand.from_command(command, partial(self._run_command, piece, command))

    def _get_element_commands(self, piece, object, current_item_key):
        for command in object.get_item_command_list(current_item_key):
            yield FreeFnCommand.from_command(command, partial(self._run_command, piece, command, current_item_key))

    def _update_element_commands(self, piece, object, current_item_key):
        self._command_hub.push_kind_commands('element', list(self._get_element_commands(piece, object, current_item_key)))

    async def _run_command(self, current_piece, command, *args, **kw):
        if command.more_params_are_required(*args, *kw):
            piece = await self._params_editor(current_piece, command, args, kw)
        else:
            piece = await command.run(*args, **kw)
        if piece is None:
            return
        await self._open_piece(piece)
        self._history.append(piece)

    async def _open_piece(self, piece):
        object = await self._object_registry.resolve_async(piece)
        self._current_item_observer = observer = _CurrentItemObserver(self, piece, object)
        layout = await self._view_producer_registry.produce_layout(piece, object, command_hub=None)
        view = await layout.create_view()
        self._view_opener.open(view)
        self._current_piece = piece
        self._current_object = object
        self._current_layout = layout
        self._command_hub.update()

    @command('go_backward')
    async def _go_backward(self):
        try:
            piece = self._history.move_backward()
        except IndexError:
            return
        await self._open_piece(piece)

    @command('go_forward')
    async def _go_forward(self):
        try:
            piece = self._history.move_forward()
        except IndexError:
            return
        await self._open_piece(piece)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.view_registry.register_type(
            htypes.navigator.navigator,
            NavigatorLayout.from_data,
            services.ref_registry,
            services.object_registry,
            services.view_producer_registry,
            services.module_command_registry,
            services.async_ref_resolver,
            services.params_editor,
            )
