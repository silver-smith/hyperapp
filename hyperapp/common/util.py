import functools
import itertools
from dateutil.tz import tzutc, tzlocal


DATETIME_FORMAT = '%d.%m.%Y %H:%M:%S'


# https://wiki.python.org/moin/PythonDecoratorLibrary
# note that this decorator ignores **kwargs
def memoize(obj):
    cache = obj.cache = {}
 
    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        if args not in cache:
            cache[args] = obj(*args, **kwargs)
        return cache[args]
    return memoizer
  

class cached_property(object):
    'Turns decorated method into caching property (method is called once on first access to property).'

    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__
        self.__doc__ = method.__doc__

    def __get__(self, inst, cls):
        if inst is None:
            return self
        result = self.method(inst)
        setattr(inst, self.name, result)
        return result


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

# from itertools recipes
def flatten(list_of_lists):
    "Flatten one level of nesting"
    return list(itertools.chain.from_iterable(list_of_lists))


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
