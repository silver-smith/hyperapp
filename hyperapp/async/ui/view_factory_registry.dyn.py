from collections import defaultdict

from hyperapp.common.module import Module

from . import htypes
from .code_registry import CodeRegistry


class AvailableViewRegistry:

    def __init__(self, mosaic):
        self._mosaic = mosaic
        self._dir_to_factory_list = defaultdict(list)

    def add_view(self, dir, piece):
        view_piece_ref = self._mosaic.put(piece)
        factory_piece = htypes.view_factory_registry.fixed_view_factory(view_piece_ref)
        self._dir_to_factory_list[tuple(dir)].append(factory_piece)

    def add_factory(self, dir, piece):
        self._dir_to_factory_list[tuple(dir)].append(piece)

    def is_fixed_factory(self, factory_piece):
        return isinstance(factory_piece, htypes.view_factory_registry.fixed_view_factory)

    def list_dir(self, dir):
        return self._dir_to_factory_list.get(tuple(dir), [])


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.view_factory_registry = CodeRegistry('view_factory', services.async_web, services.types)
        services.available_view_registry = AvailableViewRegistry(services.mosaic)

        services.view_factory_registry.register_actor(
            htypes.view_factory_registry.fixed_view_factory, self._fixed_view_factory, services.async_web)

    async def _fixed_view_factory(self, piece, object, async_web):
        return await async_web.summon(piece.view_ref)
