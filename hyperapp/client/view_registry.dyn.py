import logging
from collections import defaultdict, namedtuple

from hyperapp.client.async_registry import run_awaitable_factory
from hyperapp.client.module import ClientModule

from .async_capsule_registry import AsyncCapsuleRegistry, AsyncCapsuleResolver

_log = logging.getLogger(__name__)


class NoSuitableProducer(Exception):
    pass


class AvailableObjectLayouts:

    _Rec = namedtuple('_Rec', 'name layout_rec_maker')

    def __init__(self):
        self._category_to_rec_list = defaultdict(list)

    def register(self, category_list, name, layout_rec_maker):
        rec = self._Rec(name, layout_rec_maker)
        for category in category_list:
            self._category_to_rec_list[category].append(rec)

    def category_name_list(self, category):
        return [rec.name for rec in self._category_to_rec_list[category]]

    def get_layout_rec_maker(self, category, name):
        for rec in self._category_to_rec_list[category]:
            if rec.name == name:
                return rec.layout_rec_maker
        raise RuntimeError(f"Unknown producer: {category}.{name}")


class ObjectLayoutProducer:

    def __init__(self, default_object_layouts, object_layout_association, object_layout_registry):
        self._default_object_layouts = default_object_layouts
        self._object_layout_association = object_layout_association
        self._object_layout_registry = object_layout_registry

    async def produce_layout(self, object, command_hub, piece_opener):
        layout_ref = None
        for category in reversed(object.category_list):
            try:
                layout_ref = self._object_layout_association[category]
                assert 0  # todo: resolve to layout_rec
            except KeyError:
                pass
        if not layout_ref:
            for category in reversed(object.category_list):
                name_list = self._default_object_layouts.category_name_list(category)
                if name_list:
                    layout_rec_maker = self._default_object_layouts.get_layout_rec_maker(category, name_list[0])
                    layout_rec = await layout_rec_maker(object)
                    break
            else:
                raise NoSuitableProducer(f"No producers are registered for categories {object.category_list}")
        return (await self._object_layout_registry.resolve_async(layout_rec, object, command_hub, piece_opener))


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
        services.object_layout_registry = view_registry = AsyncCapsuleRegistry('object_layout', services.type_resolver)
        services.object_layout_resolver = view_resolver = AsyncCapsuleResolver(services.async_ref_resolver, services.object_layout_registry)
        services.object_layout_producer = ObjectLayoutProducer(
            services.default_object_layouts, services.object_layout_association, services.object_layout_registry)
