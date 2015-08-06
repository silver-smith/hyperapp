from PySide import QtCore, QtGui
from util import uni2str, key_match, key_match_any
from list_object import ListObject
from view_command import command
import view
from line_list_panel import LineListPanel
import line_edit
import list_view


class Handle(list_view.Handle):

    def __init__( self, object, key=None, order_column_id=None,
                  first_visible_row=None, elements=None, select_first=True, prefix=None ):
        assert prefix is None or isinstance(prefix, basestring), repr(prefix)
        list_view.Handle.__init__(self, object, key, order_column_id, first_visible_row, elements, select_first)
        self.prefix = prefix

    def construct( self, parent ):
        print 'narrower construct', parent, self.object.get_title(), self.object, repr(self.key), repr(self.prefix)
        return View(parent, self.object, self.key, self.order_column_id,
                    self.first_visible_row, self.elements, self.select_first, self.prefix)

    def __repr__( self ):
        return 'narrower.Handle(%s/%r/%r)' % (uni2str(self.object.get_title()), uni2str(self.key), self.prefix)


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

    def need_elements_count( self, elements_count, force_load ):
        # base may need more elements, but we do not know how much until they are loaded
        return self._base.need_elements_count(elements_count, force_load)

    def run_command( self, command_id, initiator_view, **kw ):
        return self._base.run_command(command_id, initiator_view, **kw)


class View(LineListPanel):

    def __init__( self, parent, obj, key, order_column_id, first_visible_row, elements, select_first, prefix ):
        line_edit_handle = line_edit.Handle(prefix)
        list_handle = list_view.Handle(obj, key, order_column_id, first_visible_row, elements, select_first)
        LineListPanel.__init__(self, parent, line_edit_handle, list_handle)
        self._base_obj = self._list_view.get_object()
        self._update_prefix(prefix or '')
        self._line_edit.textEdited.connect(self._on_text_edited)

    def handle( self ):
        list_handle = self._list_view.handle()
        return Handle(self._base_obj,
                      list_handle.key, list_handle.selected_keys, list_handle.select_first,
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
