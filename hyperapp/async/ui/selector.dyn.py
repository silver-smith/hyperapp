import logging

from hyperapp.common.module import Module

from . import htypes
from .command import command
from .ui_object import Object
from .code_registry import CodeRegistry

log = logging.getLogger(__name__)


class ObjectMethodCallback:

    @classmethod
    async def from_piece(cls, piece, mosaic, async_web, object_factory):
        object = await object_factory.invite(piece.object_ref)
        kw = {
            arg.name: await async_web.summon(arg.value_ref)
            for arg in piece.bound_arguments
            }
        return cls(mosaic, object, piece.method, kw)

    def __init__(self, mosaic, object, method_name, kw):
        self._mosaic = mosaic
        self._object = object
        self._method_name = method_name
        self._kw = kw

    @property
    def piece(self):
        object_ref = self._mosaic.put(self._object.piece)
        bound_arguments = [
            htypes.selector.bound_argument(name, self._mosaic.put(value))
            for name, value in self._kw.items()
            ]
        return htypes.selector.object_method_callback(object_ref, self._method_name, bound_arguments)

    async def run(self, item):
        method = getattr(self._object, self._method_name)
        return await method(item, **self._kw)


class Selector(Object):

    dir_list = [
        *Object.dir_list,
        [htypes.selector.selector_d()],
        ]
    view_state_fields = ['list_view_state_ref']

    @classmethod
    async def from_piece(cls, piece, mosaic, web, object_factory, callback_registry):
        list = await object_factory.invite(piece.list_service)
        callback = await callback_registry.invite(piece.callback)
        return cls(mosaic, web, list, callback)

    def __init__(self, mosaic, web, list, callback):
        super().__init__()
        self._mosaic = mosaic
        self._web = web
        self._list = list
        self._callback = callback
        
    @property
    def piece(self):
        list_ref = self._mosaic.put(self._list.piece)
        callback_ref = self._mosaic.put(self._callback.piece)
        return htypes.selector.selector(list_ref, callback_ref)

    @property
    def title(self):
        return f"Selector: {self._list.title}"

    @property
    def command_list(self):
        return [
            *self._list.command_list,
            *super().command_list,
            ]

    @property
    def list_object(self):
        return self._list

    @command
    async def select(self, list_view_state_ref):
        list_state = self._web.summon(list_view_state_ref)
        log.info("Selector: select: %r", list_state.current_key)
        item = await self._list.item_by_key(list_state.current_key)
        log.info("Selector: selected item: %r", item)
        return await self._callback.run(item)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._mosaic = services.mosaic

        self._callback_registry = CodeRegistry('selector_callback', services.async_web, services.types)
        self._callback_registry.register_actor(
            htypes.selector.object_method_callback,
            ObjectMethodCallback.from_piece,
            services.mosaic,
            services.async_web,
            services.object_factory,
            )
        services.object_registry.register_actor(
            htypes.selector.selector,
            Selector.from_piece,
            services.mosaic,
            services.web,
            services.object_factory,
            self._callback_registry,
            )
        services.callback_registry = self._callback_registry
        services.make_selector_callback_ref = self.make_selector_callback_ref

    def make_selector_callback_ref(self, method, **kw):
        object = method.__self__
        object_ref = self._mosaic.put(object.piece)
        method_name = method.__func__.__name__
        bound_arguments = [
            htypes.selector.bound_argument(name, self._mosaic.put(value))
            for name, value in kw.items()
            ]
        callback = htypes.selector.object_method_callback(object_ref, method_name, bound_arguments)
        return self._mosaic.put(callback)
