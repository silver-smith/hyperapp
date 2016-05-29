import weakref
from functools import partial
from datetime import datetime
from dateutil.tz import tzutc
from ..common.util import is_list_inst


class XPathNotFound(RuntimeError):
    pass


class Path(object):

    def __init__( self, path ):
        assert is_list_inst(path, str), repr(path)
        self.path = path

    def raise_not_found( self ):
        raise XPathNotFound(self.path)

    def check_empty( self ):
        if self.path:
            self.raise_not_found()

    def pop_str( self ):
        if not self.path:
            self.raise_not_found()
        part = self.path[0]
        self.path = self.path[1:]
        return part

    def pop_int_opt( self, none_str='' ):
        s = self.pop_str()
        if s == none_str:
            return None
        try:
            return int(s)
        except ValueError:
            self.raise_not_found()

    def pop_int( self ):
        v = self.pop_int_opt()
        if v is None:
            self.raise_not_found()
        return v


def path_part_to_str( val, none_str='' ):
    if val is None:
        return none_str
    else:
        return str(val)

def utcnow():
    return datetime.now(tzutc())


class _KeyedRef(weakref.ref):

    __slots__ = "key",

    def __new__( type, ob, callback, key ):
        self = weakref.ref.__new__(type, ob, callback)
        self.key = key
        return self

    def __init__(self, ob, callback, key):
        weakref.ref.__init__(self, ob, callback)


class WeakValueMultiDict(object):

    def __init__( self ):
        self.data = {}  # key -> _KeyedRef list

    def add( self, key, value ):
        l = self.data.setdefault(key, [])
        wr = _KeyedRef(value, partial(self._remove, weakref.ref(self)), key)
        l.append(wr)

    def remove( self, key, value ):
        cleaned = []
        for wr in self.data.get(key, []):
            v = wr()
            if v is not None and v != value:
                cleaned.append(wr)
        self.data[key] = cleaned
        
    def get( self, key ):
        l = []
        for wr in self.data.get(key, []):
            value = wr()
            if value is not None:
                l.append(value)
        return l

    def items( self ):
        for key, value in self.data.items():
            for wr in value:
                item = wr()
                if item:
                    yield (key, item)
            
    @staticmethod
    def _remove( self_wr, wr ):
        self = self_wr()
        if self:
            l = self.data.get(wr.key)
            if l is None: return
            l.remove(wr)
            if not l:
                del self.data[wr.key]


class MultiDict(object):

    def __init__( self ):
        self.data = {}  # key -> value list

    def add( self, key, value ):
        l = self.data.setdefault(key, [])
        l.append(value)

    def remove( self, key, value ):
        l = self.data[key]
        l.remove(value)
        
    def get( self, key ):
        return self.data[key]

    def items( self ):
        for key, values in self.data.items():
            for value in value:
                yield (key, value)
