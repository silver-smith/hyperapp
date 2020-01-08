import asyncio
import logging
from collections import namedtuple
from functools import partial

from PySide2 import QtCore, QtWidgets

from hyperapp.common.htypes import resource_key_t
from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.ref import ref_repr
from hyperapp.client.util import make_async_action
from hyperapp.client.module import ClientModule

from . import htypes
from .view_handler import RootVisualItem, ViewHandler
from .layout_registry import LayoutViewProducer

_log = logging.getLogger(__name__)


class RootHandler(ViewHandler):

    _WindowRec = namedtuple('_WindowRec', 'handler')

    @classmethod
    async def from_data(cls, state, path, ref_registry, view_resolver):
        self = cls(ref_registry, view_resolver, path)
        await self._async_init(state.window_ref_list)
        return self

    def __init__(self, ref_registry, view_resolver, path):
        super().__init__(path)
        self._ref_registry = ref_registry
        self._view_resolver = view_resolver
        self._window_list = None

    async def _async_init(self, window_ref_list):
        self._window_rec_list = [
            await self._create_window_rec(idx, ref)
            for idx, ref in enumerate(window_ref_list)
            ]

    def get_view_ref(self):
        window_ref_list = [rec.handler.get_view_ref() for rec in self._window_rec_list]
        root_layout = htypes.root_layout.root_layout(window_ref_list)
        return self._ref_registry.register_object(root_layout)

    async def create_view(self):
        self._window_list = window_list = [
            await rec.handler.create_view()
            for rec in self._window_rec_list
            ]
        for window in window_list:
            window.show()
        return window_list

    async def visual_item(self):
        children = [
            await rec.handler.visual_item()
            for rec in self._window_rec_list
            ]
        return RootVisualItem('Root', children=[
            child.to_item(idx, f'window#{idx}')
            for idx, child in enumerate(children)
            ])

    # def get_current_commands(self):
    #     try:
    #         active_window_handler = next(
    #             rec.handler for rec, window
    #                 in zip(self._window_rec_list, self._window_list)
    #                 if window.isActiveWindow()
    #             )
    #     except StopIteration:
    #         return super().get_current_commands()
    #     else:
    #         return self._get_current_commands_with_child(active_window_handler)

    def collect_view_commands(self):
        return self._collect_view_commands_with_children(
            rec.handler for rec in self._window_list)

    async def _create_window_rec(self, idx, ref):
        handler = await self._view_resolver.resolve(ref, [*self._path, idx])
        return self._WindowRec(handler)


class LayoutManager:

    def __init__(
            self,
            view_producer_registry,
            view_registry,
            ):
        self._view_producer_registry = view_producer_registry
        self._view_registry = view_registry
        self._root_handler = None
        self._window_list = None

    async def create_layout_views(self, root_view):
        # root path is expected by layout editor to be [0]
        self._root_handler = handler = await self._view_registry.resolve_async(root_view, [0])
        self._window_list = await handler.create_view()

    @property
    def root_handler(self):
        return self._root_handler

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
            )
        services.view_registry.register_type(
            htypes.root_layout.root_layout, RootHandler.from_data, services.ref_registry, services.view_resolver)
        services.view_producer = ViewProducer(layout_manager)
        services.view_opener = ViewOpener(layout_manager)
