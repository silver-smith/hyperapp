import logging
import importlib
from PySide2 import QtCore, QtWidgets

from hyperapp.client.util import DEBUG_FOCUS, call_after, focused_index, key_match
from hyperapp.client.module import ClientModule
from . import htypes
from .view import View

log = logging.getLogger(__name__)


# orientation constants
horizontal = 'horizontal'
vertical = 'vertical'


def orient2qt(orient):
    if orient == horizontal:
        return QtCore.Qt.Horizontal
    if orient == vertical:
        return QtCore.Qt.Vertical
    assert False, repr(orient)  # vertical or horizontal is expected


def qt2orient(orient):
    if orient == QtCore.Qt.Horizontal:
        return horizontal
    if orient == QtCore.Qt.Vertical:
        return vertical
    assert False, repr(orient)  # Unexpected qt orientation


def splitter_handle(x, y, orientation, focused=0, sizes=None):
    return htypes.splitter.splitter_handle(SplitterView.view_id, x, y, orientation=orientation, focused=0, sizes=sizes or [])


class SplitterView(QtWidgets.QSplitter, View):

    view_id = 'splitter'

    @classmethod
    async def from_state(cls, locale, state, parent, view_registry):
        x = await view_registry.resolve_async(locale, state.x)
        y = await view_registry.resolve_async(locale, state.y)
        return cls(parent, x, y, state.orientation, state.focused, state.sizes)

    def __init__(self, parent, x, y, orient, focused, sizes):
        QtWidgets.QSplitter.__init__(self, orient2qt(orient))
        View.__init__(self, parent)
        self._to_focus = focused  # will be used when become set visible
        self._focused = focused  # will be used by get_widget_to_focus before actual focus is received
        self._x = x
        self._y = y
        self._set_child(0, self._x)
        self._set_child(1, self._y)
        if sizes:
            self.setSizes(sizes)
        QtWidgets.QApplication.instance().focusChanged.connect(self._on_focus_changed)

    def _set_child(self, idx, view, focus=False):
        view.set_parent(self)
        w = view.get_widget()
        self.insertWidget(idx, w)
        if focus:
            if DEBUG_FOCUS: log.info('*** splitter: focusing new child self=%r view=%r w=%r', self, view, w)
            view.ensure_has_focus()

    def get_state(self):
        if DEBUG_FOCUS:
            log.info('*** splitter.handle self=%r focused=%r focused-widget=%r',
                     self, self._focused, self._get_view(self._focused).get_widget() if self._focused is not None else None)
        return splitter_handle(
            x=self._x.get_state(),
            y=self._y.get_state(),
            orientation=qt2orient(self.orientation()),
            focused=self._focused or 0,
            sizes=self.sizes())

    def get_current_child(self):
        if DEBUG_FOCUS: log.info('  * splitter.get_current_child self=%r focused=%r', self, self._focused)
        if self._focused is not None:
            return self._get_view(self._focused)
        else:
            return None

    def view_changed(self, child):
        if DEBUG_FOCUS:
            log.info('*** splitter.view_changed self=%r child=%r x/y=%r child-widget=%r', self, child, 0 if child == self._x else 1, child.get_widget())
        if self._x is None or self._y is None: return  # constructing right now
        sizes = self.sizes()
        if child == self._x:
            w = self.widget(0)
            if w is not child.get_widget():
                w.setParent(None)  # can not destroy it immediately, do it this way
                w.deleteLater()
                self._set_child(0, self._x, focus=True)
                self.setSizes(sizes)
        elif child == self._y:
            w = self.widget(1)
            if w is not child.get_widget():
                w.setParent(None)
                w.deleteLater()
                self._set_child(1, self._y, focus=True)
                self.setSizes(sizes)
        else:
            assert False, child  # Unknown child view
        View.view_changed(self)

    def open(self, handle):
        focused = self._focused_index()
        self._get_view(focused).open(handle)

    def pick_arg(self, kind):
        if self._focused is None: return
        another_view = self._get_view(1 - self._focused)
        obj = another_view.get_object()
        if obj and kind.matches(obj):
            return obj
        else:
            return None

    def _on_focus_changed(self, old, new):
        if not self.isVisible(): return
        focused = self._focused_index(default=None)
        if focused is not None and focused != self._focused:
            if DEBUG_FOCUS: log.info('--- splitter._on_focus_changed: received _focused self=%r focused=%r', self, focused)
            self._focused = focused
            View.view_changed(self)

    def _focused_index(self, default=0):
        return focused_index(self, [self._x.get_widget(), self._y.get_widget()], default)

    def _get_view(self, idx):
        if idx == 0:
            return self._x
        elif idx == 1:
            return self._y
        else:
            assert False, idx  # expected 0 or 1

    def setVisible(self, visible):
        if DEBUG_FOCUS:
            log.info('*** splitter.setVisible self=%r visible=%r self._to_focus=%r to-focus-widget=%r actual-focus=%r focused-widget=%r',
                      self, visible, self._to_focus, self._get_view(self._to_focus).get_widget() if self._to_focus is not None else None,
                      self._focused_index(), self._get_view(self._focused_index()).get_widget())
        QtWidgets.QWidget.setVisible(self, visible)
        if visible and self._to_focus is not None:
            if DEBUG_FOCUS:
                log.info('  will focus self=%r to_focus=%r to-focus-widget=%r', self, self._to_focus, self._get_view(self._to_focus).get_widget())
            self._get_view(self._to_focus).ensure_has_focus()
            # and leave self._to_focus set for later focusInEvent - required for active tab to work
            self._focused = self._to_focus
            self._to_focus = None

    def focusInEvent(self, evt):
        if DEBUG_FOCUS:
            log.info('*** splitter.focusInEvent self=%r to_focus=%r to-focus-widget=%r',
                     self, self._to_focus, self._get_view(self._to_focus).get_widget() if self._to_focus is not None else None)
        QtWidgets.QSplitter.focusInEvent(self, evt)

    def focusOutEvent(self, evt):
        if DEBUG_FOCUS: log.info('*** splitter.focusOutEvent self=%r', self)
        QtWidgets.QSplitter.focusOutEvent(self, evt)


## class MonolithView(SplitterView):

##     def open(self, handle):
##         return View.open(self, handle)


def map_current(handle, mapper):
    if handle.focused == 0:
        return splitter_handle(mapper(handle.x), handle.y, handle.orientation, handle.focused, handle.sizes)
    elif handle.focused == 1:
        return splitter_handle(handle.x, mapper(handle.y), handle.orientation, handle.focused, handle.sizes)
    else:
        assert False, repr(handle.focused)  # 0 or 1 is expected


def split(orient):
    def mapper(handle):
        if handle.view_id == SplitterView.view_id:
            return map_current(handle, mapper)
        else:
            return splitter_handle(handle, handle, orient)
    return mapper


def unsplit(handle):
    if handle.view_id != SplitterView.view_id:
        return None
    if handle.focused == 0:
        child = handle.x
    else:
        child = handle.y
    if child.view_id != SplitterView.view_id:
        return child
    return map_current(handle, unsplit)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.view_registry.register(SplitterView.view_id, SplitterView.from_state, services.view_registry)
