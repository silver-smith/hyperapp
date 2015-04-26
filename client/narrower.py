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
    def from_resp( cls, obj, resp ):
        return cls(list_view.Handle(obj))

    def __init__( self, list_handle, prefix=None ):
        composite.Handle.__init__(self)
        assert isinstance(list_handle, list_view.Handle), repr(list_handle)
        self.list_handle = list_handle
        self.prefix = prefix

    def get_child_handle( self ):
        return self.list_handle

    def construct( self, parent ):
        print 'narrower construct', parent, self.list_handle, self.prefix
        return View(parent, self.list_handle, self.prefix)

    def __repr__( self ):
        return 'narrower.Handle(%r/%r)' % (self.list_handle, self.prefix)


# todo: subscription
class FilteredListObj(ListObject):

    def __init__( self, base, prefix ):
        ListObject.__init__(self)
        self._base = base
        self._prefix = prefix

    def get_title( self ):
        return 'filtered(%r, %s)' % (self._prefix, self._base.get_title())

    def get_commands( self ):
        return self._base.get_commands()

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

    def __init__( self, parent, list_handle, prefix ):
        LineListPanel.__init__(self, parent, line_edit.Handle(prefix), list_handle)
        self._base_obj = self._list_view.get_object()
        self._update_prefix(prefix or '')
        self._line_edit.textEdited.connect(self._on_text_edited)

    def handle( self ):
        return Handle(list_view.Handle(self._base_obj, self._list_view.get_current_key(), self._list_view.selected_keys()),
                      self._line_edit.text())

    def get_title( self ):
        return self._base_obj.get_title()

    def get_object( self ):
        return self._base_obj

    def _set_prefix( self, prefix ):
        self._line_edit.setText('')
        self._update_prefix('')

    def _update_prefix( self, text ):
        key = self._list_view.get_current_key()
        if text:
            self._list_view.set_object(FilteredListObj(self._base_obj, text))
        else:
            self._list_view.set_object(self._base_obj)
        self._list_view.set_current_key(key, select_first=True)
        self.cancel_narrowing.setEnabled(text != '')

    def _on_text_edited( self, text ):
        self._update_prefix(text)

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

    @command('Wider', 'Cancel narrowing', ['Escape'], enabled=False)
    def cancel_narrowing( self ):
        if self._line_edit.text():
            self._set_prefix('')

    def eventFilter( self, obj, evt ):
        if self._line_edit.text() and key_match(evt, 'Space'):
            self._fill_common_prefix()
            return True
        return LineListPanel.eventFilter(self, obj, evt)

    def _fill_common_prefix( self ):
        dir = self._list_view.get_object()
        elements = dir.get_fetched_elements()
        if not elements: return
        common = elements[0].key
        for elt in elements[1:]:
            while not elt.key.startswith(common):
                common = common[:-1]
        self._line_edit.setText(common)

    def __del__( self ):
        print '~narrower', self._base_obj.get_title(), self


view_registry.register_view('list_narrower', Handle.from_resp)
