# navigator component - container keeping navigation history and allowing go backward and forward

import logging
import asyncio
from PySide import QtCore, QtGui

from hyperapp.common.util import is_list_inst
from hyperapp.client.util import key_match, key_match_any
from hyperapp.client.command import command
from hyperapp.client.view import View
from hyperapp.client import list_view
from . import htypes
from .history_list import HistoryList

log = logging.getLogger(__name__)


HISTORY_LIST_RESOURCE_ID = ['client_module', 'navigator', 'HistoryList']
MAX_HISTORY_SIZE = 100


class NavigatorView(View):

    view_id = 'navigator'

    @classmethod
    async def from_state(cls, locale, state, parent, view_registry):
        child = await view_registry.resolve_async(locale, state.history[state.current_pos].handle)
        return cls(locale, parent, view_registry, child,
                   state.history[:state.current_pos],
                   list(reversed(state.history[state.current_pos + 1:])))

    def __init__(self, locale, parent, view_registry, child, backward_history=None, forward_history=None):
        assert isinstance(child, View), repr(child)
        assert backward_history is None or is_list_inst(backward_history, htypes.navigator.item), repr(backward_history)
        assert forward_history is None or is_list_inst(forward_history, htypes.navigator.item), repr(forward_history)
        super().__init__(parent)
        self._locale = locale
        self._view_registry = view_registry
        self._backward_history = backward_history or []     # item_type list
        self._forward_history = forward_history or []   # item_type list
        self._child = child
        self._child.set_parent(self)

    def get_state(self):
        history = self._backward_history \
           + [htypes.navigator.item(self._child.get_title(), self._child.get_state())] \
           + list(reversed(self._forward_history))
        return htypes.navigator.state(self.view_id, history, current_pos=len(self._backward_history))

    def get_widget(self):
        if self._child is None: return None  # constructing right now
        return self._child.get_widget()

    def set_child(self, handle):
        #print 'history open', self._backward_history, self._forward_history, handle
        self._forward_history = []
        self._add2history(self._backward_history, self._child)
        if len(self._backward_history) > MAX_HISTORY_SIZE:
            self._backward_history = self._backward_history[-MAX_HISTORY_SIZE:]
        asyncio.async(self._open(handle))

    def get_current_child(self):
        return self._child

    def open(self, handle):
        self.set_child(handle)

    def hide_current(self):
        self._go_back()

    async def _open(self, handle):
        self._child = await self._view_registry.resolve_async(self._locale, handle, self)
        self._parent().view_changed(self)
        object = self._child.get_object()
#        if object:
#            object.subscribe(self)

    @command('go_back')
    def go_back(self):
        log.info('   history back len(back_history)=%r len(forward_history)=%r', len(self._backward_history), len(self._forward_history))
        self._go_back()

    def _go_back(self):
        if not self._backward_history:
            return False
        self._add2history(self._forward_history, self._child)
        asyncio.async(self._open(self._pop_history(self._backward_history)))

    @command('go_forward')
    def go_forward(self):
        log.info('   history forward len(back_history)=%r len(forward_history)=%r', len(self._backward_history), len(self._forward_history))
        if not self._forward_history:
            return False
        self._add2history(self._backward_history, self._child)
        asyncio.async(self._open(self._pop_history(self._forward_history)))

    def _add2history(self, history, view):
        if isinstance(view, list_view.View) and isinstance(view.get_object(), HistoryList):
            return  # do not add history list itself to history
        history.append(htypes.navigator.item(view.get_title(), view.get_state()))

    def _pop_history(self, history):
        item = history.pop()
        return item.handle

    @command('open_history')
    def open_history(self):
        state = self.get_state()
        object = htypes.navigator.history_list(HistoryList.impl_id, state.history)
        self.open(htypes.navigator.history_list_handle('list', object, resource_id=HISTORY_LIST_RESOURCE_ID, sort_column_id='idx', key=state.current_pos))

    def __del__(self):
        log.info('~navigator')
