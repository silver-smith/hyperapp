# navigator component - container keeping navigation history and allowing go backward and forward

from PySide import QtCore, QtGui
from ..common.interface import tInt, tString, TList, Field, TRecord, tHandle, list_handle_type
from .util import key_match, key_match_any
from .view_registry import view_registry
from .view_command import command
from . import view
from . import composite
from . import list_view
from .history_list import HistoryRow, HistoryList


MAX_HISTORY_SIZE = 100


item_type = TRecord([
    Field('title', tString),
    Field('handle', tHandle),
    ])

data_type = TRecord([
    Field('history', TList(item_type)),
    Field('current_pos', tInt),
    ])


class Item(object):

    @classmethod
    def from_handle( cls, handle ):
        return cls(handle.get_title(), handle.get_module_ids(), handle.to_data())

    @classmethod
    def from_data( cls, rec ):
        return cls(rec.title, [], rec.handle)

    def __init__( self, title, required_module_ids, handle_data ):
        self.title = title
        self.required_module_ids = required_module_ids
        self.handle_data = handle_data

    def to_data( self ):
        return item_type.instantiate(self.title, self.handle_data)

    def load( self ):
        handle = view_registry.resolve(self.handle_data)
        object = handle.get_object()
        if object:
            object.server_subscribe()
        return handle


class Handle(composite.Handle):

    @classmethod
    def from_data( cls, rec ):
        items = [Item.from_data(item_rec) for item_rec in rec.history]
        child_handle = items[rec.current_pos].load()
        return cls(child_handle, items[:rec.current_pos], items[rec.current_pos + 1:])

    def __init__( self, child_handle, backward_history=None, forward_history=None ):
        composite.Handle.__init__(self, [child_handle])
        self.child = child_handle
        self.backward_history = backward_history or []   # Item list
        self.forward_history = forward_history or []     # Item list
        self.required_module_ids = self._collect_required_module_ids()

    def to_data( self ):
        history = [item.to_data() for item in self.backward_history] \
           + [item_type.instantiate(self.child.get_title(), self.child.to_data())] \
           + [item.to_data() for item in self.forward_history]
        return data_type.instantiate(history, current_pos=len(self.backward_history))

    def get_child_handle( self ):
        return self.child

    def get_module_ids( self ):
        return self.required_module_ids

    def construct( self, parent ):
        print 'navigator construct', parent, self.child
        return View(parent, self.child, self.backward_history[:], self.forward_history[:])

    def _collect_required_module_ids( self ):
        module_ids = set(composite.Handle.get_module_ids(self))
        for item in self.backward_history + self.forward_history:
            module_ids.update(set(item.required_module_ids))
        return list(module_ids)


class View(composite.Composite):

    history_handle_type = list_handle_type('navigator_history', tInt)

    def __init__( self, parent, child_handle, backward_history=None, forward_history=None ):
        composite.Composite.__init__(self, parent)
        self._back_history = backward_history or []     # Item list
        self._forward_history = forward_history or []   # Item list
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
        self._add2history(self._back_history, self._child.handle())
        if len(self._back_history) > MAX_HISTORY_SIZE:
            self._back_history = self._back_history[-MAX_HISTORY_SIZE:]
        self._open(handle)

    def get_current_child( self ):
        return self._child

    def open( self, handle ):
        self.set_child(handle)

    def hide_current( self ):
        self._go_back()

    def _open( self, handle ):
        self._child = handle.construct(self)
        self._parent().view_changed(self)

    @command('Go back', 'Go backward to previous page', ['Escape', 'Alt+Left'])
    def go_back( self ):
        print '   history back', len(self._back_history), len(self._forward_history)
        self._go_back()

    def _go_back( self ):
        if not self._back_history:
            return False
        self._add2history(self._forward_history, self._child.handle())
        self._open(self._pop_history(self._back_history))

    @command('Go forward', 'Go forward to next page', 'Alt+Right')
    def go_forward( self ):
        print '   history forward', len(self._back_history), len(self._forward_history)
        if not self._forward_history:
            return False
        self._add2history(self._back_history, self._child.handle())
        self._open(self._pop_history(self._forward_history))

    def _add2history( self, history, handle ):
        if isinstance(handle.get_object(), HistoryList): return  # do not add history list itself to history
        history.append(Item.from_handle(handle))

    def _pop_history( self, history ):
        item = history.pop()
        return item.load()

    @command('History', 'Open history', 'Ctrl+H')
    def open_history( self ):
        idx = len(self._back_history)
        current_handle = self._child.handle()
        items = self._back_history + [Item.from_handle(current_handle)] + list(reversed(self._forward_history))
        rows = [HistoryRow(idx, item) for idx, item in enumerate(items)]
        object = HistoryList(rows)
        self.open(list_view.Handle(self.history_handle_type, object, sort_column_id='idx', key=idx))

    def __del__( self ):
        print '~navigator'
