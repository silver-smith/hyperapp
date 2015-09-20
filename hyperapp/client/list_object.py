from functools import total_ordering
from PySide import QtCore, QtGui
from ..common.util import is_list_inst, dt2local_str
from .command import Command
from .object import ObjectObserver, Object


class ListObserver(ObjectObserver):

    def process_fetch_result( self, result ):
        pass

    def diff_applied( self, diff ):
        pass

    
class ListDiff(object):

    @classmethod
    def add_one( cls, key, element ):
        return cls(key, key, [element])

    @classmethod
    def add_many( cls, key, elements ):
        return cls(key, key, elements)

    @classmethod
    def append_many( cls, elements ):
        return cls.add_many(None, elements)

    @classmethod
    def delete( cls, key ):
        return cls(key, key, [])

    @classmethod
    def decode( cls, key_column_id, rec ):
        return cls(rec.start_key, rec.end_key, [Element.decode(key_column_id, None, elt) for elt in rec.elements])

    def __init__( self, start_key, end_key, elements ):
        # keys == None means append
        self.start_key = start_key  # replace elements from this one
        self.end_key = end_key      # up to (and including) this one
        self.elements = elements    # with these elemenents

    def __repr__( self ):
        return 'ListDiff(%r-%r>%r)' % (self.start_key, self.end_key, self.elements)


@total_ordering
class Element(object):

    @classmethod
    def decode( cls, key_column_id, sort_column_id, rec ):
        key = getattr(rec.row, key_column_id)
        if sort_column_id is None:
            order_key = None
        else:
            order_key = getattr(rec.row, sort_column_id)
        commands = map(Command.decode, rec.commands)
        return cls(key, rec.row, commands, order_key)

    def __init__( self, key, row, commands, order_key=None ):
        assert is_list_inst(commands, Command), repr(commands)
        self.key = key
        self.row = row
        self.commands = commands
        if order_key is not None:
            self.order_key = order_key

    def __eq__( self, other ):
        if isinstance(other, Element):
            return self.order_key == other.order_key
        else:
            return self.order_key == other

    def __lt__( self, other ):
        if isinstance(other, Element):
            return self.order_key < other.order_key
        else:
            return self.order_key < other

    def clone_with_sort_column( self, sort_column_id ):
        order_key = getattr(self.row, sort_column_id)
        return Element(self.key, self.row, self.commands, order_key)
 

class Slice(object):

    def __init__( self, sort_column_id, from_key, direction, elements, bof, eof ):
        assert isinstance(sort_column_id, basestring), repr(sort_column_id)
        assert direction in ['asc', 'desc'], repr(direction)
        assert is_list_inst(elements, Element), repr(elements)
        self.sort_column_id = sort_column_id
        self.from_key = from_key
        self.direction = direction
        self.elements = elements
        self.bof = bof
        self.eof = eof

    def clone_with_elements( self, elements ):
        return Slice(self.sort_column_id, self.from_key, self.direction, elements, self.bof, self.eof)


class ListObject(Object):

    def get_columns( self ):
        raise NotImplementedError(self.__class__)

    def get_key_column_id( self ):
        raise NotImplementedError(self.__class__)

    def get_default_sort_column_id( self ):
        raise NotImplementedError(self.__class__)
    
    def subscribe_and_fetch_elements( self, observer, sort_column_id, key, desc_count, asc_count ):
        raise NotImplementedError(self.__class__)

    def fetch_elements( self, sort_column_id, key, desc_count, asc_count ):
        raise NotImplementedError(self.__class__)

    def run_element_command( self, command_id, element_key, initiator_view ):
        return self.run_command(command_id, initiator_view, element_key=element_key)

    def _notify_fetch_result( self, result ):
        assert isinstance(result, Slice), repr(result)
        for observer in self._observers:
            observer.process_fetch_result(result)

    def _notify_diff_applied( self, diff ):
        assert isinstance(diff, ListDiff), repr(diff)
        for observer in self._observers:
            observer.diff_applied(diff)
