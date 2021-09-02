import logging
import weakref
from PySide2 import QtCore, QtWidgets

from .view_command import ViewCommander
from .object import ObjectObserver
from .util import DEBUG_FOCUS, focused_index
from .module import ClientModule

log = logging.getLogger(__name__)


class View(ObjectObserver, ViewCommander):

    CmdPanelHandleCls = None  # registered by cmd_view

    def __init__(self):
        ObjectObserver.__init__(self)
        ViewCommander.__init__(self)

    def get_state(self):
        raise NotImplementedError(self.__class__)

    @property
    def object(self):
        return None

    def object_changed(self):
        pass

    @property
    def qt_widget(self):
        return self

    def get_current_child(self):
        return None

    def get_current_view(self):
        child = self.get_current_child()
        if child:
            return child.get_current_view()
        else:
            return self

    @property
    def title(self):
        view = self.get_current_child()
        if view:
            return view.title
        object = self.object
        if object:
            return object.title
        return 'Untitled'

    def has_focus(self):
        return focused_index(None, [self]) == 0

    def ensure_has_focus(self):
        if DEBUG_FOCUS: log.info('  * view.ensure_has_focus %r', self)
        if not self.has_focus():
            self.acquire_focus()

    def acquire_focus(self):
        w = self.get_widget_to_focus()
        if DEBUG_FOCUS: log.info('*** view.acquire_focus %r w=%r', self, w)
        assert w.focusPolicy() & QtCore.Qt.StrongFocus == QtCore.Qt.StrongFocus, (self, w, w.focusPolicy())  # implement get_current_child or your own get_widget_to_focus otherwise
        w.setFocus()

    def get_widget_to_focus(self):
        child = self.get_current_child()
        if DEBUG_FOCUS: log.info('  * view.get_widget_to_focus %r child=%r', self, child)
        if child:
            return child.get_widget_to_focus()
        return self.get_widget()
