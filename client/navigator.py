# navigator component - container keeping navigation history and allowing go backward and forward

from PySide import QtCore, QtGui
from util import key_match, key_match_any
from attribute import Attr, StrAttrType
from command import command, command_owner_meta_class
import view
from composite import Composite
import list_view


MAX_HISTORY_SIZE = 100


class Handle(view.Handle):

    def __init__( self, child_handle, backward_history=None, forward_history=None ):
        view.Handle.__init__(self)
        self.child = child_handle
        self.backward_history = backward_history or []
        self.forward_history = forward_history or []

    def title( self ):
        return self.child.title()

    def construct( self, parent ):
        print 'navigator construct', parent, self.child
        return View(parent, self.child, self.backward_history[:], self.forward_history[:])


class View(Composite):

    __metaclass__ = command_owner_meta_class

    def __init__( self, parent, child_handle, backward_history=None, forward_history=None ):
        Composite.__init__(self, parent)
        self._back_history = backward_history or []
        self._forward_history = forward_history or []
        self._child = None  # get_widget may be called from next line
        self._child = child_handle.construct(self)

    def handle( self ):
        return Handle(self._child.handle(), self._back_history, self._forward_history)

    def get_widget( self ):
        if self._child is None: return None  # constructing right now
        return self._child.get_widget()

    def set_child( self, handle ):
        #print 'history open', self._back_history, self._forward_history, handle
        self._forward_history = []
        if not isinstance(self._child.current_dir(), HistoryList):
            self._back_history.append(self._child.handle())
            if len(self._back_history) > MAX_HISTORY_SIZE:
                self._back_history = self._back_history[-MAX_HISTORY_SIZE:]
        self._open(handle)

    def current_child( self ):
        return self._child

    def open( self, handle ):
        self.set_child(handle)

    def hide_current( self ):
        self._go_back()

    def _open( self, handle ):
        self._child = handle.construct(self)
        self._parent().view_changed(self)

    @command(['Escape', 'Alt+Left'], 'Go back')
    def go_back( self ):
        print '   history back', self._back_history, self._forward_history
        self._go_back()

    def _go_back( self ):
        if not self._back_history:
            return False
        if not isinstance(self._child.current_dir(), HistoryList):
            self._forward_history.append(self._child.handle())
        self._open(self._back_history.pop())

    @command('Alt+Right', 'Go forward')
    def go_forward( self ):
        print '   history forward', self._back_history, self._forward_history
        if not self._forward_history:
            return False
        if not isinstance(self._child.current_dir(), HistoryList):
            self._back_history.append(self._child.handle())
        self._open(self._forward_history.pop())

    ## @command('Ctrl+H', 'History')
    ## def open_history( self ):
    ##     idx = len(self._back_history)
    ##     current_handle = self._child.handle()
    ##     history = HistoryList(self._back_history + [current_handle] + list(reversed(self._forward_history)))
    ##     return list_view.Handle(history, idx)
