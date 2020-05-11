import logging
from collections import defaultdict, namedtuple

from hyperapp.client.async_registry import run_awaitable_factory
from hyperapp.client.module import ClientModule

from .async_capsule_registry import AsyncCapsuleRegistry, AsyncCapsuleResolver

_log = logging.getLogger(__name__)


class ObjectLayoutRegistry:

    _Rec = namedtuple('_Rec', 'name factory args kw')

    def __init__(self):
        self._category_to_rec_list = defaultdict(list)

    def register(self, category_list, name, factory, *args, **kw):
        rec = self._Rec(name, factory, args, kw)
        for category in category_list:
            self._category_to_rec_list[category].append(rec)

    def category_name_list(self, category):
        return [rec.name for rec in self._category_to_rec_list[category]]

    async def produce_layout(self, object, command_hub, piece_opener):
        for category in reversed(object.category_list):
            try:
                rec = self._category_to_rec_list[category][0]
            except IndexError:
                continue
            _log.info('Producing object layout for object %s using %s(%s, %s)',
                      object, rec.factory, rec.args, rec.kw)
            return (await run_awaitable_factory(rec.factory, object, command_hub, piece_opener, *rec.args, **rec.kw))
        raise RuntimeError(f"No producers are registered for categories {object.category_list}")
            

class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_layout_overrides = {}  # resource key -> layout ref
        # todo: rename view to layout
        services.available_view_registry = {}  # id -> view ref, views available to add to layout
        services.view_registry = view_registry = AsyncCapsuleRegistry('view', services.type_resolver)
        services.view_resolver = view_resolver = AsyncCapsuleResolver(services.async_ref_resolver, view_registry)
        services.object_layout_registry = ObjectLayoutRegistry()
