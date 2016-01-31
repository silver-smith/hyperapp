from PySide import QtCore, QtGui
from ..common.htypes import tInt, TList, Field, TRecord
from .util import DEBUG_FOCUS, call_after, key_match
from .view_command import command
from . import view
from . import composite
from . import splitter
from . import navigator


data_type = TRecord([
    Field('tabs', TList(navigator.data_type)),
    Field('current_tab', tInt),
    ])


class Handle(composite.Handle):

    @classmethod
    def from_data( cls, rec ):
        return cls([navigator.Handle.from_data(hrec) for hrec in rec.tabs], rec.current_tab)

    def __init__( self, children, current_idx=0 ):
        composite.Handle.__init__(self, children)
        self.current_idx = current_idx  # child index, 0..

    def to_data( self ):
        tabs = [h.to_data() for h in self.children]
        return data_type.instantiate(tabs=tabs, current_tab=self.current_idx)

    def get_current_child( self ):
        return self.children[self.current_idx]

    def construct( self, parent ):
        print 'tab_view construct', parent, len(self.children), self.current_idx
        return View(parent, self.children, self.current_idx)

    def map_current( self, mapper ):
        idx = self.current_idx
        return Handle(self.children[:idx] + [mapper(self.children[idx])] + self.children[idx+1:], idx)


class View(QtGui.QTabWidget, view.View):

    def __init__( self, parent, children, current_idx ):
        QtGui.QTabWidget.__init__(self)
        view.View.__init__(self, parent)
        self.tabBar().setFocusPolicy(QtCore.Qt.NoFocus)
        self.setElideMode(QtCore.Qt.ElideMiddle)
        self._children = []  # view list
        for handle in children:
            v = handle.construct(self)
            self.addTab(v.get_widget(), v.get_title())
            self._children.append(v)
        self.setCurrentIndex(current_idx)
        self.currentChanged.connect(self._on_current_changed)

    def handle( self ):
        return Handle([view.handle() for view in self._children], self.currentIndex())

    def get_current_child( self ):
        idx = self.currentIndex()
        if idx == -1 or idx >= len(self._children): return None  # changing right now
        return self._children[idx]

    def view_changed( self, child ):
        idx = self.currentIndex()
        if idx == -1: return  # constructing right now
        if idx >= len(self._children) or child is not self._children[idx]:
            return  # this child may be deleted right now
        w = self.widget(idx)
        if child is not self._children[idx] or w is not child.get_widget():
            if DEBUG_FOCUS: print '*** tab_view.view_changed: replacing tab', self, idx, child
            self.removeTab(idx)
            w.deleteLater()
            self.insertTab(idx, child.get_widget(), child.get_title())
            self.setCurrentIndex(idx)
            child.ensure_has_focus()
        self.setTabText(idx, child.get_title())
        view.View.view_changed(self)  # notify parents

    def open( self, handle ):
        # here we assume that child is a navigator view
        idx = self.currentIndex()
        self._children[idx].open(handle)  # handle it to navigator

    def _on_current_changed( self, idx ):
        view.View.view_changed(self)

    def setVisible( self, visible ):
        if DEBUG_FOCUS: print '*** tab_view.setVisible', self, visible, '(current tab#%d)' % self.currentIndex()
        QtGui.QTabWidget.setVisible(self, visible)

    @command('Duplicate tab', 'Duplicate current tab', 'Ctrl+T')
    def duplicate_tab( self ):
        idx = self.currentIndex()
        view = self._children[idx]
        new_view = view.handle().construct(self)
        self._insert_tab(idx + 1, new_view)
        self._parent().view_changed(self)

    @command('Close tab', 'Close current tab', 'Ctrl+F4')
    def close_tab( self ):
        if len(self._children) == 1: return  # never close last tab
        idx = self.currentIndex()
        self._remove_tab(idx)
        if idx >= len(self._children):
            idx -= 1
        view.View.view_changed(self)  # notify parents

    @command('&Split horizontally', 'Split horizontally', 'Alt+S')
    def split_horizontally( self ):
        self._map_current(splitter.split(splitter.horizontal))

    @command('Split &vertically', 'Split vertically', 'Shift+Alt+S')
    def split_vertically( self ):
        self._map_current(splitter.split(splitter.vertical))

    @command('&Unsplit', 'Unsplit', 'Alt+U')
    def unsplit( self ):
        self._map_current(splitter.unsplit)

    def _map_current( self, mapper ):
        idx = self.currentIndex()
        handle = mapper(self._children[idx].handle())
        if not handle: return
        self._remove_tab(idx)
        child = handle.construct(self)
        self._insert_tab(idx, child)
        child.ensure_has_focus()
        view.View.view_changed(self)  # notify parents

    def _remove_tab( self, idx ):
        w = self.widget(idx)
        # remove child first so later view_changed calls from child being deleted may be ignored:
        del self._children[idx]
        self.removeTab(idx)
        w.deleteLater()

    def _insert_tab( self, idx, child ):
        self.insertTab(idx, child.get_widget(), child.get_title())
        self._children.insert(idx, child)
        self.setCurrentIndex(idx)

    def __del__( self ):
        print '~tab_view'
