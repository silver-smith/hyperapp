from hyperapp.common.htypes import resource_key_t

LOCALE = 'en'


def map_columns_to_view(resource_resolver, type_ref, column_list):
    for column in column_list:
        resource_key = resource_key_t(type_ref, ['column', column.id])
        resource = resource_resolver.resolve(resource_key, LOCALE)
        if resource:
            if not resource.is_visible:
                continue
            text = resource.text
        else:
            text = column.id
        yield column.to_view_column(text)
