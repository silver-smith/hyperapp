import asyncio
import abc
from functools import total_ordering
from PySide import QtCore, QtGui
from ..common.util import is_list_inst, dt2local_str
from ..common.htypes import ListInterface
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

    def __init__( self, start_key, end_key, elements ):
        # keys == None means append
        self.start_key = start_key  # replace elements from this one
        self.end_key = end_key      # up to (and including) this one
        self.elements = elements    # with these elemenents

    def __repr__( self ):
        return 'ListDiff(%r-%r>%r)' % (self.start_key, self.end_key, self.elements)


@total_ordering
class Element(object):

    def __init__( self, key, row, commands, order_key=None ):
        assert is_list_inst(commands, Command), repr(commands)
        self.key = key
        self.row = row
        self.commands = commands
        if order_key is not None:
            self.order_key = order_key

    def to_data( self, iface ):
        assert isinstance(iface, ListInterface), repr(iface)
        return iface.Element(self.row, [cmd.to_data() for cmd in self.commands])

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
        assert isinstance(sort_column_id, str), repr(sort_column_id)
        assert direction in ['asc', 'desc'], repr(direction)
        assert is_list_inst(elements, Element), repr(elements)
        self.sort_column_id = sort_column_id
        self.from_key = from_key
        self.direction = direction
        self.elements = elements
        self.bof = bof
        self.eof = eof

    def __eq__( self, other ):
        if not isinstance(other, Slice):
            return False
        return (self.sort_column_id == other.sort_column_id
                and self.from_key == other.from_key
                and self.direction == other.direction
                and self.elements == other.elements
                and self.bof == other.bof
                and self.eof == other.eof)

    def __repr__( self ):
        return ('Slice(sort_column_id=%r from_key=%r direction=%r bof=%r eof=%r %d elements %s)'
                % (self.sort_column_id, self.from_key, self.direction, self.bof, self.eof, len(self.elements),
                   'from %r to %r' % (self.elements[0].key, self.elements[-1].key) if self.elements else ''))

    def to_data( self, iface ):
        assert isinstance(iface, ListInterface), repr(iface)
        elements = [elt.to_data(iface) for elt in self.elements]
        return iface.Slice(self.sort_column_id, self.from_key, self.direction, elements, self.bof, self.eof)

    def clone_with_elements( self, elements ):
        return Slice(self.sort_column_id, self.from_key, self.direction, elements, self.bof, self.eof)


class ListObject(Object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_columns( self ):
        pass

    @abc.abstractmethod
    def get_key_column_id( self ):
        pass

    @asyncio.coroutine
    @abc.abstractmethod
    def fetch_elements( self, sort_column_id, key, desc_count, asc_count ):
        pass

    # currently unused
    @asyncio.coroutine
    def run_element_command( self, command_id, element_key ):
        return (yield from self.run_command(command_id, element_key=element_key))

    def _notify_fetch_result( self, slice ):
        assert isinstance(slice, Slice), repr(slice)
        for observer in self._observers:
            observer.process_fetch_result(slice)

    def _notify_diff_applied( self, diff ):
        assert isinstance(diff, ListDiff), repr(diff)
        for observer in self._observers:
            observer.diff_applied(diff)
