import itertools
from dateutil.tz import tzutc, tzlocal


DATETIME_FORMAT = '%d.%m.%Y %H:%M:%S'
  

def is_iterable_inst(val, cls):
    if not isinstance(val, (list, tuple)):
        return False
    for elt in val:
        if not isinstance(elt, cls):
            return False
    return True

def is_list_inst(val, cls):
    if not isinstance(val, list):
        return False
    for elt in val:
        if not isinstance(elt, cls):
            return False
    return True

def is_list_list_inst(val, cls):
    if not isinstance(val, list):
        return False
    for elt in val:
        if not is_list_inst(elt, cls):
            return False
    return True

def is_tuple_inst(val, cls):
    if not isinstance(val, tuple):
        return False
    for elt in val:
        if not isinstance(elt, cls):
            return False
    return True


def is_dict_inst(value, key_cls, val_cls):
    if not isinstance(value, dict):
        return False
    for key, val in value.items():
        if not isinstance(key, key_cls):
            return False
        if not isinstance(val, val_cls):
            return False
    return True


# from itertools recipes
def flatten(list_of_lists):
    "Flatten one level of nesting"
    return list(itertools.chain.from_iterable(list_of_lists))


def merge_dicts(list_of_dicts):
    result = {}
    for d in list_of_dicts:
        result.update(d)
    return result


def single(iter):
    all = list(iter)
    assert len(all) == 1, repr(all)  # Exactly one item is expected
    return all[0]


# todo: quote/unquote '|' chars
def encode_path(path):
    return '|'.join(path)

def decode_path(path_str):
    return path_str.split('|')

# todo: quote/unquote '|' chars
def encode_route(route):
    return '|'.join(route)

def decode_route(route_str):
    return route_str.split('|')

def dt_naive_to_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tzutc())  # naive -> utc
    else:
        return dt

def dt2local_str(dt):
    if dt is None: return ''
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tzutc())  # naive -> utc
    return dt.astimezone(tzlocal()).strftime(DATETIME_FORMAT)
