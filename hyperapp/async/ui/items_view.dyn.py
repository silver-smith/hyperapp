
LOCALE = 'en'


def map_columns_to_view(resource_resolver, object):
    for column in object.columns:
        resource_key = object.resource_key(['column', column.id])
        resource = resource_resolver.resolve(resource_key, LOCALE)
        if resource:
            if not resource.is_visible:
                continue
            text = resource.text
        else:
            text = column.id
        yield column.to_view_column(text)
