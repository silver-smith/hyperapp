from dateutil.tz import tzutc, tzlocal


DATETIME_FORMAT = '%d.%m.%Y %H:%M:%S'


def is_list_inst( val, cls ):
    if not isinstance(val, list):
        return False
    for elt in val:
        if not isinstance(elt, cls):
            return False
    return True

# stringified path is included into persistent id, which requires binary str, not unicode
def path2str( path ):
    return '/'.join(path).encode('utf-8')

def str2path( path_str ):
    return path_str.decode('utf-8').split('/')

def dt2local_str( dt ):
    if dt is None: return ''
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tzutc())  # naive -> utc
    return dt.astimezone(tzlocal()).strftime(DATETIME_FORMAT)
