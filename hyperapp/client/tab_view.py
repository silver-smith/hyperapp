import logging
import asyncio
from PySide import QtCore, QtGui
from ..common.util import is_list_inst
from ..common.htypes import tInt, TList, Field, TRecord, tHandle
from .util import DEBUG_FOCUS, call_after, key_match
from .module import Module
from .command import command
from . import view
from . import splitter

log = logging.getLogger(__name__)


def get_state_type():
    return this_module.state_type


class View(QtGui.QTabWidget, view.View):

    @classmethod
    @asyncio.coroutine
    def from_state( cls, locale, state, view_registry ):
        children = []
        for tab_state in state.tabs:
            child = yield from view_registry.resolve(locale, tab_state)
            children.append(child)
        return cls(locale, view_registry, children, state.current_tab)

    @staticmethod    
    def map_current( state, mapper ):
        idx = state.current_tab
        return this_module.state_type(state.tabs[:idx] + [mapper(state.tabs[idx])] + state.tabs[idx+1:], idx)

    def __init__( self, locale, view_registry, children, current_idx ):
        assert is_list_inst(children, view.View), repr(children)
        QtGui.QTabWidget.__init__(self)
        view.View.__init__(self)
        self._locale = locale
        self._view_registry = view_registry
        self.tabBar().setFocusPolicy(QtCore.Qt.NoFocus)
        self.setElideMode(QtCore.Qt.ElideMiddle)
        self._children = []  # view list
        for child in children:
            child.set_parent(self)
            self.addTab(child.get_widget(), child.get_title())
            self._children.append(child)
        self.setCurrentIndex(current_idx)
        self.currentChanged.connect(self._on_current_changed)

    def get_state( self ):
        return this_module.state_type([view.get_state() for view in self._children], self.currentIndex())

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
            if DEBUG_FOCUS: log.info('*** tab_view.view_changed: replacing tab self=%r idx=%r child=%r', self, idx, child)
            self.removeTab(idx)
            w.deleteLater()
            self.insertTab(idx, child.get_widget(), child.get_title())
            self.setCurrentIndex(idx)
            child.ensure_has_focus()
        self.setTabText(idx, child.get_title())
        view.View.view_changed(self)  # notify parents

    def open( self, handle ):
        idx = self.currentIndex()
        self._children[idx].open(handle)

    def _on_current_changed( self, idx ):
        view.View.view_changed(self)

    def setVisible( self, visible ):
        if DEBUG_FOCUS: log.info('*** tab_view.setVisible self=%r visible=%r current-tab#=%d', self, visible, self.currentIndex())
        QtGui.QTabWidget.setVisible(self, visible)

    @command('duplicate_tab')
    @asyncio.coroutine
    def duplicate_tab( self ):
        idx = self.currentIndex()
        state = self._children[idx].get_state()
        new_view = yield from self._view_registry.resolve(self._locale, state, self)
        self._insert_tab(idx + 1, new_view)
        self._parent().view_changed(self)

    @command('close_tab')
    def close_tab( self ):
        if len(self._children) == 1: return  # never close last tab
        idx = self.currentIndex()
        self._remove_tab(idx)
        if idx >= len(self._children):
            idx -= 1
        view.View.view_changed(self)  # notify parents

    @command('split_horizontally')
    @asyncio.coroutine
    def split_horizontally( self ):
        yield from self._map_current(splitter.split(splitter.horizontal))

    @command('split_vertically')
    @asyncio.coroutine
    def split_vertically( self ):
        yield from self._map_current(splitter.split(splitter.vertical))

    @command('unsplit')
    @asyncio.coroutine
    def unsplit( self ):
        yield from self._map_current(splitter.unsplit)

    @asyncio.coroutine
    def _map_current( self, mapper ):
        idx = self.currentIndex()
        state = mapper(self._children[idx].get_state())
        if not state: return
        self._remove_tab(idx)
        child = yield from self._view_registry.resolve(self._locale, state, self)
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
        log.info('~tab_view')


class ThisModule(Module):

    def __init__( self, services ):
        Module.__init__(self, services)
        self.state_type = TRecord([
            Field('tabs', TList(tHandle)),
            Field('current_tab', tInt),
            ])
