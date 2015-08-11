from PySide import QtCore, QtGui
from common.util import is_list_inst, dt2local_str
from object import ObjectObserver, Object


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
        return cls(rec.start_key, rec.end_key, [Element.decode(key_column_id, elt) for elt in rec.elements])

    def __init__( self, start_key, end_key, elements ):
        # keys == None means append
        self.start_key = start_key  # replace elements from this one
        self.end_key = end_key      # up to (and including) this one
        self.elements = elements    # with these elemenents

    def __repr__( self ):
        return 'ListDiff(%r-%r>%r)' % (self.start_key, self.end_key, self.elements)


class Element(object):

    @classmethod
    def decode( cls, key_column_id, rec ):
        key = getattr(rec.row, key_column_id)
        return cls(key, rec.row, rec.commands)

    def __init__( self, key, row, commands ):
        self.key = key
        self.row = row
        self.commands = commands


class Slice(object):

    def __init__( self, sort_column_id, elements, bof, eof ):
        assert isinstance(sort_column_id, basestring), repr(sort_column_id)
        assert is_list_inst(elements, Element), repr(elements)
        self.sort_column_id = sort_column_id
        self.elements = elements
        self.bof = bof
        self.eof = eof


class ListObject(Object):

    def get_columns( self ):
        raise NotImplementedError(self.__class__)

    def get_key_column_id( self ):
        raise NotImplementedError(self.__class__)

    def get_default_order_column_id( self ):
        raise NotImplementedError(self.__class__)

    def subscribe_and_fetch_elements( self, observer, sort_column_id, key, desc_count, asc_count ):
        raise NotImplementedError(self.__class__)

    def fetch_elements( self, sort_column_id, key, desc_count, asc_count ):
        raise NotImplementedError(self.__class__)

    def run_element_command( self, command_id, element_key, initiator_view ):
        return self.run_command(command_id, initiator_view, element_key=element_key)

    def _notify_fetch_result( self, result ):
        #assert isinstance(diff, ListDiff), repr(diff)  # may also be interface update Record
        for observer in self._observers:
            observer.process_fetch_result(result)

    def _notify_diff_applied( self, diff ):
        #assert isinstance(diff, ListDiff), repr(diff)  # may also be interface update Record
        for observer in self._observers:
            observer.diff_applied(diff)
