from PySide import QtCore, QtGui
from common.util import dt2local_str
from object import Object


class ListObject(Object):

    def get_columns( self ):
        raise NotImplementedError(self.__class__)

    def element_count( self ):
        raise NotImplementedError(self.__class__)

    def need_elements_count( self, elements_count, force_load ):
        raise NotImplementedError(self.__class__)

    @staticmethod
    def _find_key_column( columns ):
        for idx, col in enumerate(columns):
            if col.id == 'key':
                return idx
        assert False, 'No "key" column'

    def run_element_command( self, command_id, element_key, initiator_view ):
        return self.run_command(command_id, initiator_view, element_key=element_key)

    def _notify_diff_applied( self, diff ):
        assert isinstance(diff, ListDiff), repr(diff)
        for observer in self._observers:
            observer.diff_applied(diff)
