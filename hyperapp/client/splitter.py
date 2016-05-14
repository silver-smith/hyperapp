import logging
from PySide import QtCore, QtGui
from ..common.interface.splitter import tSplitterHandle
from .util import DEBUG_FOCUS, call_after, focused_index, key_match
from . import view
from . import composite
from .view_registry import view_registry

log = logging.getLogger(__name__)


# orientation constants
horizontal = 'horizontal'
vertical = 'vertical'


def orient2qt( orient ):
    if orient == horizontal:
        return QtCore.Qt.Horizontal
    if orient == vertical:
        return QtCore.Qt.Vertical
    assert False, repr(orient)  # vertical or horizontal is expected

def qt2orient( orient ):
    if orient == QtCore.Qt.Horizontal:
        return horizontal
    if orient == QtCore.Qt.Vertical:
        return vertical
    assert False, repr(orient)  # Unexpected qt orientation


class Handle(composite.Handle):

    @classmethod
    def from_data( cls, contents, server=None ):
        x = view_registry.resolve(contents.x, server)
        y = view_registry.resolve(contents.y, server)
        return cls(x, y, contents.orientation)

    def __init__( self, x, y, orient, focused=0, sizes=None ):
        composite.Handle.__init__(self, [x, y])
        assert focused in [0, 1]
        self.x = x  # handle of first child
        self.y = y  # handle of second child
        self.orient = orient
        self.focused = focused
        self.sizes = sizes

    def to_data( self ):
        return tSplitterHandle('splitter', self.x.to_data(), self.y.to_data(), self.orient)

    def construct( self, parent ):
        log.info('splitter construct parent=%r orient=%r focused=%r', parent, self.orient, self.focused)
        return View(parent, self.x, self.y, self.orient, self.focused, self.sizes)

    def get_child_handle( self ):
        if self.focused == 0:
            return self.x
        else:
            return self.y

    def map_current( self, mapper ):
        if self.focused == 0:
            return Handle(mapper(self.x), self.y, self.orient, self.focused, self.sizes)
        elif self.focused == 1:
            return Handle(self.x, mapper(self.y), self.orient, self.focused, self.sizes)
        else:
            assert False, repr(self.focused)  # 0 or 1 is expected


class MonolithHandle(Handle):

    def construct( self, parent ):
        log.info('splitter monolith construct parent=%r orient=%r focused=%r', parent, self.orient, self.focused)
        return MonolithView(parent, self.x, self.y, self.orient, self.focused, self.sizes)


class View(QtGui.QSplitter, view.View):

    def __init__( self, parent, x, y, orient, focused, sizes ):
        QtGui.QSplitter.__init__(self, orient2qt(orient))
        view.View.__init__(self, parent)
        self._to_focus = focused  # will be used when become set visible
        self._focused = focused  # will be used by get_widget_to_focus before actual focus is received
        self._x = self._y = None  # view_changed is firing during construction
        self._x = x.construct(self)
        self._set_child(0, self._x)
        self._y = y.construct(self)
        self._set_child(1, self._y)
        if sizes:
            self.setSizes(sizes)
        QtGui.QApplication.instance().focusChanged.connect(self._on_focus_changed)

    def _set_child( self, idx, view, focus=False ):
        w = view.get_widget()
        self.insertWidget(idx, w)
        if focus:
            if DEBUG_FOCUS: log.info('*** splitter: focusing new child self=%r view=%r w=%r', self, view, w)
            view.ensure_has_focus()

    def handle( self ):
        if DEBUG_FOCUS:
            log.info('*** splitter.handle self=%r focused=%r focused-widget=%r',
                     self, self._focused, self._get_view(self._focused).get_widget() if self._focused is not None else None)
        return self._handle_class()(self._x.handle(), self._y.handle(), qt2orient(self.orientation()),
                                    self._focused or 0, self.sizes())

    def _handle_class( self ):
        return Handle

    def get_current_child( self ):
        if DEBUG_FOCUS: log.info('  * splitter.get_current_child self=%r focused=%r', self, self._focused)
        if self._focused is not None:
            return self._get_view(self._focused)
        else:
            return None

    def view_changed( self, child ):
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
        view.View.view_changed(self)

    def open( self, handle ):
        focused = self._focused_index()
        self._get_view(focused).open(handle)

    def pick_arg( self, kind ):
        if self._focused is None: return
        another_view = self._get_view(1 - self._focused)
        obj = another_view.get_object()
        if obj and kind.matches(obj):
            return obj
        else:
            return None

    def _on_focus_changed( self, old, new ):
        if not self.isVisible(): return
        focused = self._focused_index(default=None)
        if focused is not None and focused != self._focused:
            if DEBUG_FOCUS: log.info('--- splitter._on_focus_changed: received _focused self=%r focused=%r', self, focused)
            self._focused = focused
            view.View.view_changed(self)

    def _focused_index( self, default=0 ):
        return focused_index(self, [self._x.get_widget(), self._y.get_widget()], default)

    def _get_view( self, idx ):
        if idx == 0:
            return self._x
        elif idx == 1:
            return self._y
        else:
            assert False, idx  # expected 0 or 1

    def setVisible( self, visible ):
        if DEBUG_FOCUS:
            log.info('*** splitter.setVisible self=%r visible=%r self._to_focus=%r to-focus-widget=%r actual-focus=%r focused-widget=%r',
                      self, visible, self._to_focus, self._get_view(self._to_focus).get_widget() if self._to_focus is not None else None,
                      self._focused_index(), self._get_view(self._focused_index()).get_widget())
        QtGui.QWidget.setVisible(self, visible)
        if visible and self._to_focus is not None:
            if DEBUG_FOCUS:
                log.info('  will focus self=%r to_focus=%r to-focus-widget=%r', self, self._to_focus, self._get_view(self._to_focus).get_widget())
            self._get_view(self._to_focus).ensure_has_focus()
            # and leave self._to_focus set for later focusInEvent - required for active tab to work
            self._focused = self._to_focus
            self._to_focus = None

    def focusInEvent( self, evt ):
        if DEBUG_FOCUS:
            log.info('*** splitter.focusInEvent self=%r to_focus=%r to-focus-widget=%r',
                     self, self._to_focus, self._get_view(self._to_focus).get_widget() if self._to_focus is not None else None)
        QtGui.QSplitter.focusInEvent(self, evt)

    def focusOutEvent( self, evt ):
        if DEBUG_FOCUS: log.info('*** splitter.focusOutEvent self=%r', self)
        QtGui.QSplitter.focusOutEvent(self, evt)


class MonolithView(View):

    def _handle_class( self ):
        return MonolithHandle

    def open( self, handle ):
        return view.View.open(self, handle)


def split( orient ):
    def mapper( handle ):
        if isinstance(handle, Handle):
            return handle.map_current(mapper)
        else:
            return Handle(handle, handle, orient)
    return mapper

def unsplit( handle ):
    if isinstance(handle, Handle):
        h = handle.get_child_handle()
        if isinstance(h, Handle):
            return handle.map_current(unsplit)
        else:
            return h


view_registry.register('splitter', Handle.from_data)
