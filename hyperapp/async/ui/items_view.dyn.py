
LOCALE = 'en'


def map_columns_to_view(lcs, object):
    for column in object.columns:
        text = column.id
        yield column.to_view_column(text)
