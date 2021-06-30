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

    def __init__(self, parent=None):
        ObjectObserver.__init__(self)
        ViewCommander.__init__(self)
        self._parent = weakref.ref(parent) if parent is not None else None

    def set_parent(self, parent):
        assert isinstance(parent, View), repr(parent)
        self._parent = weakref.ref(parent)

    def get_state(self):
        raise NotImplementedError(self.__class__)

    def object_changed(self):
        self.view_changed()

    def get_widget(self):
        return self

    def get_current_child(self):
        return None

    def get_current_view(self):
        child = self.get_current_child()
        if child:
            return child.get_current_view()
        else:
            return self

    def get_command_list(self):
        command_list = ViewCommander.get_command_list(self)
        child = self.get_current_child()
        if child:
            command_list += child.get_command_list()
        return command_list

    def get_shortcut_ctx_widget(self, view):
        return view.get_widget()

    @property
    def title(self):
        view = self.get_current_child()
        if view:
            return view.title
        return 'Untitled'

    def object_selected(self, obj):
        return self._parent().object_selected(obj)

    def open(self, handle):
        self._parent().open(handle)

    def replace_view(self, mapper):
        return mapper(self.handle())

    def view_changed(self, view=None):
        log.debug('-- View.view_changed self=%s/%r view=%r', id(self), self, view)
        if self._parent:
            self._parent().view_changed(self)

    def view_commands_changed(self, command_kinds):
        if self._parent:
            self._parent().view_commands_changed(command_kinds)

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

    def _cls2name(self, cls):
        return cls.__module__ + '.' + cls.__class__.__name__
