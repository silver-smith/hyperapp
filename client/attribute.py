import time
from util import dt2local_str


class AttrType(object):

    def attr2str( self, val ):
        return unicode(val)


class StrAttrType(AttrType):

    def attr2str( self, val ):
        if isinstance(val, unicode):
            return val
        elif isinstance(val, str):
            return unicode(val, 'utf-8')
        else:
            assert False, repr(val)  # unicode or str is expected


class MonospacedStrAttrType(StrAttrType):
    pass


class IntAttrType(AttrType):
    pass


class BoolAttrType(AttrType):

    def attr2str( self, val ):
        if val:
            return 'yes'
        else:
            return 'no'


class DateTimeAttrType(AttrType):

    def attr2str( self, val ):
        return dt2local_str(val)


class Attr(object):

    def __init__( self, name, type, title=None ):
        assert isinstance(type, AttrType), repr(type)
        self.name = name
        self.type = type
        self.title = title or name

    def attr2str( self, val ):
        if val is None:
            return None
        else:
            return self.type.attr2str(val)
