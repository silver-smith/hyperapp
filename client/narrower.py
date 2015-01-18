from PySide import QtCore, QtGui
from util import key_match, key_match_any
from object import Dir
import view
import composite
from line_list_panel import LineListPanel
import line_edit
import list_view


class Handle(composite.Handle):

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
class FilteredDir(Dir):

    def __init__( self, base, prefix ):
        Dir.__init__(self)
        self._base = base
        self._prefix = prefix

    def get_title( self ):
        return 'filtered(%r, %s)' % (self._prefix, self._base.get_title())

    def key( self ):
        return self._base.key()

    def commands( self ):
        return self._base.commands()

    def get_attributes( self ):
        return self._base.get_attributes()

    def elements( self, start=None, end=None ):
        elements = []
        for elt in self._base.elements():
            key = elt.key()
            if isinstance(key, basestring) and key.lower().startswith(self._prefix.lower()):
                elements.append(elt)
        return elements[start:end]

    def parent( self ):
        return self._base.parent()


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
        if text:
            self._list_view.set_object(FilteredDir(self._base_obj, text))
        else:
            self._list_view.set_object(self._base_obj)

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
