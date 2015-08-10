from PySide import QtCore, QtGui
from util import uni2str, key_match, key_match_any
from list_object import ListObserver, Slice, ListObject
from view_command import command
from view_registry import view_registry
import view
from line_list_panel import LineListPanel
import line_edit
import list_view


class Handle(view.Handle):

    @classmethod
    def from_resp( cls, server, contents ):
        object = server.resolve_object(contents.object)
        list_handle = list_view.Handle(object, contents.key)
        return cls(object, list_handle, contents.field_id)

    def __init__( self, object, list_handle, field_id, prefix=None ):
        assert prefix is None or isinstance(prefix, basestring), repr(prefix)
        view.Handle.__init__(self)
        self.object = object
        self.list_handle = list_handle
        self.field_id = field_id
        self.prefix = prefix

    def get_object( self ):
        return self.object

    def construct( self, parent ):
        print 'narrower construct', parent, self.object.get_title(), \
          repr(self.list_handle), self.field_id, repr(self.prefix)
        return View(parent, self.object, self.list_handle, self.field_id, self.prefix)

    def __repr__( self ):
        return 'narrower.Handle(%r/%r/%r/%r)' \
          % (uni2str(self.object.get_title()), self.list_handle, self.field_id, self.prefix)


# todo: subscription
class FilteredListObj(ListObject, ListObserver):

    def __init__( self, base, field_id, prefix ):
        ListObject.__init__(self)
        self._base = base
        self._field_id = field_id  # filter by this field
        self._prefix = prefix

    def get_title( self ):
        return 'filtered(%r, %s)' % (self._prefix, self._base.get_title())

    def get_commands( self ):
        return self._base.get_commands()

    def get_columns( self ):
        return self._base.get_columns()

    def get_key_column_id( self ):
        return self._base.get_key_column_id()

    def get_default_order_column_id( self ):
        return self._base.get_default_order_column_id()
    
    def subscribe_and_fetch_elements( self, observer, sort_by_column, key, desc_count, asc_count ):
        ListObject.subscribe_local(self, observer)
        self._base.subscribe_and_fetch_elements(self, sort_by_column, key, desc_count, asc_count)

    def fetch_elements( self, sort_by_column, key, desc_count, asc_count ):
        self._base.fetch_elements(sort_by_column, key, desc_count, asc_count)

    def process_fetch_result( self, result ):
        print '-- narrower.process_fetch_result', result.bof, result.eof, len(result.elements)
        filtered = Slice(filter(self._element_matched, result.elements), result.bof, result.eof)
        if filtered.elements:
            self._notify_fetch_result(filtered)

    def _element_matched( self, element ):
        value = getattr(element.row, self._field_id)
        return value.lower().startswith(self._prefix.lower())

    def run_command( self, command_id, initiator_view, **kw ):
        return self._base.run_command(command_id, initiator_view, **kw)

    def __del__( self ):
        print '~FilteredListObj', repr(self._prefix)


class View(LineListPanel):

    def __init__( self, parent, object, list_handle, field_id, prefix ):
        self._base_obj = object
        self._field_id = field_id
        list_object = self._object4prefix(prefix)
        line_edit_handle = line_edit.Handle(prefix)
        LineListPanel.__init__(self, parent, line_edit_handle, list_handle)
        self._line_edit.textEdited.connect(self._on_text_edited)

    def handle( self ):
        list_handle = self._list_view.handle()
        return Handle(self.get_object(), list_handle, self._field_id, self._line_edit.text())

    def get_title( self ):
        return self._base_obj.get_title()

    def get_object( self ):
        return self._base_obj

    def _set_prefix( self, prefix ):
        self._line_edit.setText('')
        self._update_prefix('')

    def _object4prefix( self, prefix ):
        if prefix:
            return FilteredListObj(self._base_obj, self._field_id, prefix)
        else:
            return self._base_obj

    def _update_prefix( self, text ):
        key = self._list_view.get_current_key()
        object = self._object4prefix(text)
        if self._list_view.get_object() is not object:
            self._list_view.set_object(object)
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


view_registry.register('list_narrower', Handle.from_resp)
