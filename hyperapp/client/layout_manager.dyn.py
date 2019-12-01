import asyncio
import logging
from functools import partial

from PySide2 import QtCore, QtWidgets

from hyperapp.common.htypes import resource_key_t
from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.ref import ref_repr
from hyperapp.client.util import make_async_action
from hyperapp.client.module import ClientModule
from . import htypes
from .layout_registry import LayoutViewProducer
from .command_registry import CommandRegistry

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
            view_producer_registry,
            view_registry,
            default_state_builder,
            ):
        self._view_producer_registry = view_producer_registry
        self._view_registry = view_registry
        self._default_state_builder = default_state_builder
        self._window_list = []
        self._command_registry = CommandRegistry()
        self._window_0_handler = None

    async def build_default_layout(self, app):
        state = self._default_state_builder()
        window_state = state[0]
        self._window_0_handler = window_handler = await self._view_registry.resolve_async(window_state, [0])
        window = await window_handler.create_view(self._command_registry)
        window.show()
        self._window_list.append(window)

    @property
    def window_0_handler(self):
        return self._window_0_handler

    async def produce_view(self, piece, object, observer=None):
        return (await self._view_producer_registry.produce_view(piece, object, observer))


class ViewProducer(LayoutViewProducer):

    def __init__(self, view_producer_registry):
        self._view_producer_registry = view_producer_registry

    async def produce_view(self, piece, object, observer=None):
        return (await self._view_producer_registry.produce_view(piece, object, observer))

    async def produce_default_view(self, piece, object, observer=None):
        return (await self._view_producer_registry.produce_view(piece, object, observer))


class ViewOpener:

    def __init__(self, layout_manager):
        self._layout_manager = layout_manager

    async def open_rec(self, rec):
        await self._layout_manager.open(rec)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.layout_manager = layout_manager = LayoutManager(
            services.view_producer_registry,
            services.view_registry,
            services.default_state_builder,
            )
        services.view_producer = ViewProducer(layout_manager)
        services.view_opener = ViewOpener(layout_manager)
