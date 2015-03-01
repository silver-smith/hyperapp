from PySide import QtCore, QtGui
from util import key_match, key_match_any
from list_object import ListObject
from view_command import command
import view_registry
import view
import composite
from line_list_panel import LineListPanel
import line_edit
import list_view


class Handle(composite.Handle):

    @classmethod
    def from_obj( cls, obj ):
        return cls(list_view.Handle(obj))

    def __init__( self, list_handle ):
        composite.Handle.__init__(self)
        assert isinstance(list_handle, list_view.Handle), repr(list_handle)
        self.list_handle = list_handle

    def get_child_handle( self ):
        return self.list_handle

    def construct( self, parent ):
        print 'narrower construct', parent, self.list_handle
        return View(parent, self.list_handle)

    def __repr__( self ):
        return 'narrower.Handle(%r)' % self.list_handle


# todo: subscription
class FilteredListObj(ListObject):

    def __init__( self, base, prefix ):
        ListObject.__init__(self)
        self._base = base
        self._prefix = prefix

    def get_title( self ):
        return 'filtered(%r, %s)' % (self._prefix, self._base.get_title())

    def get_columns( self ):
        return self._base.get_columns()

    def element_count( self ):
        return len(self.get_fetched_elements())

    def get_fetched_elements( self ):
        elements = []
        for elt in self._base.get_fetched_elements():
            if isinstance(elt.key, basestring) and elt.key.lower().startswith(self._prefix.lower()):
                elements.append(elt)
        return elements

    def are_all_elements_fetched( self ):
        return self._base.are_all_elements_fetched()

    def load_elements( self, load_count ):
        required_count = self.element_count() + load_count
        while not self.are_all_elements_fetched() and self.element_count() < required_count:
            self._base.load_elements(required_count - self.element_count())

    def run_element_command( self, command_id, element_key ):
        return self._base.run_element_command(command_id, element_key)


class View(LineListPanel):

    def __init__( self, parent, list_handle ):
        LineListPanel.__init__(self, parent, line_edit.Handle(''), list_handle)
        self._base_obj = self._list_view.get_object()
        self._line_edit.textEdited.connect(self._on_text_edited)

    def handle( self ):
        return Handle(list_view.Handle(self._base_obj, self._list_view.current_key(), self._list_view.selected_keys()))

    def get_title( self ):
        return self._base_obj.get_title()

    def get_object( self ):
        return self._base_obj

    def _on_text_edited( self, text ):
        #print 'on text edited', text
        key = self._list_view.current_key()
        if text:
            self._list_view.set_object(FilteredListObj(self._base_obj, text))
        else:
            self._list_view.set_object(self._base_obj)
        self._list_view.set_current_key(key, select_first=True)

    def is_list_event( self, evt ):
        if key_match_any(evt, [
            'Period',
            'Slash',
            'Ctrl+A',
            ]):
            return True
        if not self._line_edit.text() and key_match(evt, 'Ctrl+Backspace'):
            return True
        return LineListPanel.is_list_event(self, evt)

    @command('Wider', 'Cancel narrowing', ['Escape'])
    def cancel_narrowing( self ):
        if self._line_edit.text() and key_match(evt, 'Escape'):
            self._line_edit.setText('')

    def eventFilter( self, obj, evt ):
        if self._line_edit.text() and key_match(evt, 'Space'):
            self._fill_common_prefix()
            return True
        return LineListPanel.eventFilter(self, obj, evt)

    def _fill_common_prefix( self ):
        dir = self._list_view.get_object()
        elements = dir.elements()
        if not elements: return
        common = elements[0].name
        for elt in elements[1:]:
            while not elt.name.startswith(common):
                common = common[:-1]
        self._line_edit.setText(common)

    def __del__( self ):
        print '~narrower', self._base_obj.get_title(), self


view_registry.register_view('list_narrower', Handle.from_obj)
