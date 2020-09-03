import logging
import weakref
from collections import defaultdict, namedtuple

from hyperapp.client.async_registry import run_awaitable_factory
from hyperapp.client.module import ClientModule

from .async_capsule_registry import AsyncCapsuleRegistry, AsyncCapsuleResolver

_log = logging.getLogger(__name__)


class NoSuitableProducer(Exception):
    pass


CommandOrigin = namedtuple('CommandOrigin', 'object command_id')


class ObjectLayoutConstructorRegistry:

    _Rec = namedtuple('_Rec', 'name object_type_t_set layout_data_maker')

    def __init__(self):
        self._rec_list = []

    def register(self, name, object_type_t_list, layout_data_maker):
        rec = self._Rec(name, set(object_type_t_list), layout_data_maker)
        self._rec_list.append(rec)

    def resolve(self, object_type):
        t_set = set()
        t = object_type._t
        while t:
            t_set.add(t)
            t = t.base
        for rec in self._rec_list:
            if t_set & rec.object_type_t_set:
                yield rec

    async def construct_default_layout(self, object_type, watcher, object_layout_registry):
        rec_it = self.resolve(object_type)
        try:
            rec = next(rec_it)
        except StopIteration:
            raise NoSuitableProducer(f"No default layout makers are registered for: {object_type}")
        _log.info("Use default layout: %r.", rec.name)
        layout_data = await rec.layout_data_maker(object_type)
        layout = await object_layout_registry.resolve_async(layout_data, ['root'], watcher)
        return layout


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        # todo: rename view to layout
        services.available_view_registry = {}  # id -> view ref, views available to add to layout
        services.view_registry = view_registry = AsyncCapsuleRegistry('view', services.type_resolver)
        services.view_resolver = view_resolver = AsyncCapsuleResolver(services.async_ref_resolver, view_registry)
        services.available_object_layouts = ObjectLayoutConstructorRegistry()
        services.default_object_layouts = ObjectLayoutConstructorRegistry()
        services.object_layout_association = {}  # object_type -> layout ref
        services.object_layout_registry = view_registry = AsyncCapsuleRegistry('object_layout', services.type_resolver)
        services.object_layout_resolver = view_resolver = AsyncCapsuleResolver(services.async_ref_resolver, services.object_layout_registry)
