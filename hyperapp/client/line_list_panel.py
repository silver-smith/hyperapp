# base for panels containing line edit with list view

from PySide import QtCore, QtGui
from .util import DEBUG_FOCUS, call_after, key_match, key_match_any
from .composite import Composite


class LineListPanel(Composite, QtGui.QWidget):

    def __init__( self, parent, line_handle, list_handle ):
        QtGui.QWidget.__init__(self)
        Composite.__init__(self, parent)
        self._line_edit = line_handle.construct(self)
        self._list_view = list_handle.construct(self)
        self._list_view.get_widget().setFocusPolicy(QtCore.Qt.NoFocus)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._line_edit.get_widget())
        layout.addWidget(self._list_view.get_widget())
        self.setFocusProxy(self._line_edit.get_widget())
        self.setLayout(layout)
        self._line_edit.installEventFilter(self)

    def get_current_child( self ):
        return self._list_view

    def get_widget_to_focus( self ):
        return self._line_edit

    def get_shortcut_ctx_widget( self, view ):
        return self._line_edit.get_widget()

    def is_list_event( self, evt ):
        if key_match(evt, 'Space'):
            return self._list_view.is_in_multi_selection_mode()
        return key_match_any(evt, [
            ('Up'),
            ('Down'),
            ('PageUp'),
            ('PageDown'),
            ('Return'),
            ('Ctrl+Up'),
            ('Ctrl+Down'),
            ('Ctrl+PageUp'),
            ('Ctrl+PageDown'),
            ('Ctrl+Home'),
            ('Ctrl+End'),
            ])

    def eventFilter( self, obj, evt ):
        if self.is_list_event(evt):
            self._list_view.keyPressEvent(evt)
            return True
        return QtGui.QWidget.eventFilter(self, obj, evt)

    def focusInEvent( self, evt ):
        if DEBUG_FOCUS: print '*** line_list_panel.focusInEvent', self
        QtGui.QWidget.focusInEvent(self, evt)
        ## self._line_edit.get_widget().setFocus()  # - now using setFocusProxy

    def focusOutEvent( self, evt ):
        if DEBUG_FOCUS: print '*** line_list_panel.focusOutEvent', self
        QtGui.QWidget.focusOutEvent(self, evt)
