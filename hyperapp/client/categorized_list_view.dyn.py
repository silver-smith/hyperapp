import asyncio
from ..common.interface import core as core_types
from . import narrower


CATEGORIZED_LIST_VIEW_ID = 'categorized_list'


def register_views(registry, services):
    registry.register(CATEGORIZED_LIST_VIEW_ID, resolve_categorized_list_view)

@asyncio.coroutine
def resolve_categorized_list_view(locale, handle, parent):
    for category in handle.categories:
        if category == ['initial', 'fs']:
            handle_t = core_types.handle.get_object_class(handle)
            key_t = handle_t.get_field('key').type.base_t
            narrower_handle_t = narrower.narrower_list_handle_type(key_t)
            return narrower_handle_t(
                narrower.NARROWER_VIEW_ID, handle.object, handle.resource_id, handle.sort_column_id,
                narrow_field_id='key', key=handle.key)
    assert False  # todo
