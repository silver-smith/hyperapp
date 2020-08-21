import logging
from collections import defaultdict, namedtuple

from hyperapp.client.async_registry import run_awaitable_factory
from hyperapp.client.module import ClientModule

from .async_capsule_registry import AsyncCapsuleRegistry, AsyncCapsuleResolver

_log = logging.getLogger(__name__)


class NoSuitableProducer(Exception):
    pass


class AvailableObjectLayouts:

    _Rec = namedtuple('_Rec', 'name, category_set layout_rec_maker')

    def __init__(self):
        self._rec_list = []

    def register(self, name, category_list, layout_rec_maker):
        rec = self._Rec(name, set(category_list), layout_rec_maker)
        self._rec_list.append(rec)

    def resolve(self, category_list):
        category_set = set(category_list)
        for rec in self._rec_list:
            if category_set & rec.category_set:
                yield rec


class ObjectLayoutProducer:

    def __init__(self, async_ref_resolver, default_object_layouts, object_layout_association, object_layout_registry):
        self._async_ref_resolver = async_ref_resolver
        self._default_object_layouts = default_object_layouts
        self._object_layout_association = object_layout_association
        self._object_layout_registry = object_layout_registry

    async def produce_layout(self, object, layout_watcher):
        layout_rec = None
        for category in reversed(object.category_list):
            try:
                layout_ref = self._object_layout_association[category]
            except KeyError:
                continue
            layout_rec = await self._async_ref_resolver.resolve_ref_to_object(layout_ref)
            break
        if not layout_rec:
            rec_it = self._default_object_layouts.resolve(object.category_list)
            try:
                rec = next(rec_it)
            except StopIteration:
                raise NoSuitableProducer(f"No producers are registered for categories {object.category_list}")
            layout_rec = await rec.layout_rec_maker(object)
        return (await self._object_layout_registry.resolve_async(layout_rec, [0], object, layout_watcher))


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_layout_overrides = {}  # resource key -> layout ref
        # todo: rename view to layout
        services.available_view_registry = {}  # id -> view ref, views available to add to layout
        services.view_registry = view_registry = AsyncCapsuleRegistry('view', services.type_resolver)
        services.view_resolver = view_resolver = AsyncCapsuleResolver(services.async_ref_resolver, view_registry)
        services.default_object_layouts = AvailableObjectLayouts()
        services.available_object_layouts = AvailableObjectLayouts()
        services.object_layout_association = {}  # category -> layout ref
        services.object_command_layout_association = {}  # category, command id -> layout ref
        services.object_layout_registry = view_registry = AsyncCapsuleRegistry('object_layout', services.type_resolver)
        services.object_layout_resolver = view_resolver = AsyncCapsuleResolver(services.async_ref_resolver, services.object_layout_registry)
        services.object_layout_producer = ObjectLayoutProducer(
            services.async_ref_resolver, services.default_object_layouts, services.object_layout_association, services.object_layout_registry)
