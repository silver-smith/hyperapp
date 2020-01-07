# base class for Views

import logging
import weakref
from PySide2 import QtCore, QtWidgets

from hyperapp.client.qt_keys import print_key_event
from hyperapp.client.util import DEBUG_FOCUS, focused_index
from hyperapp.client.module import ClientModule
from hyperapp.client.object import ObjectObserver
from hyperapp.client.commander import Command, Commander

log = logging.getLogger(__name__)


class ViewCommand(Command):

    @classmethod
    def from_command(cls, cmd, view, *args):
        return cls(cmd.id, cmd.kind, cmd.resource_key, cmd.enabled, cmd, weakref.ref(view), args)

    def __init__(self, id, kind, resource_key, enabled, base_cmd, view_wr, args):
        Command.__init__(self, id, kind, resource_key, enabled)
        self._base_cmd = base_cmd
        self._view_wr = view_wr  # weak ref to class instance
        self._args = args

    def __repr__(self):
        return 'ViewCommand(%r (base=%r) -> %s/%r)' % (self.id, self._base_cmd, id(self._view_wr()), self._view_wr())

    def get_view(self):
        return self._view_wr()

    async def run(self, *args, **kw):
        view = self._view_wr()
        if not view:
            return
        all_args = self._args + args
        log.debug('ViewCommand.run: %r/%r, %r, (%s, %s), view=%r', self.id, self.kind, self._base_cmd, all_args, kw, id(view))
        try:
            handle = await self._base_cmd.run(*all_args, **kw)
            ## assert handle is None or isinstance(handle, tHandle), repr(handle)  # command can return only handle
        except Exception as x:
            log.exception('Error running command %r:', self.id)
            handle = get_handle_for_error(x)
        if handle:
            view.open(handle)


class View(ObjectObserver, Commander):

    CmdPanelHandleCls = None  # registered by cmd_view

    def __init__(self, parent=None):
        ObjectObserver.__init__(self)
        Commander.__init__(self, commands_kind='view')
        self._parent = weakref.ref(parent) if parent is not None else None
        self._module_command_registry = None

    def init(self, module_command_registry):
        self._module_command_registry = module_command_registry

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

    def get_command_list(self, kinds=None):
        assert self._module_command_registry, repr(self)  # init method was not called, expected to be called by ViewRegistry.resolve
        commands = [ViewCommand.from_command(cmd, self) for cmd in Commander.get_command_list(self, kinds)]
        child = self.get_current_child()
        if child:
            commands += child.get_command_list(kinds)
        object = self.get_object()
        if object:
            commands += [ViewCommand.from_command(cmd, self) for cmd in
                         self.get_object_command_list(object, kinds) + self._module_command_registry.get_all_object_commands(object)]
        return commands

    def get_object_command_list(self, object, kinds=None):
        return object.get_command_list(kinds)

    def get_shortcut_ctx_widget(self, view):
        return view.get_widget()

    def get_title(self):
        view = self.get_current_child()
        if view:
            return view.get_title()
        object = self.get_object()
        if object:
            return object.get_title()
        return 'Untitled'

    def pick_current_refs(self):
        ref_list = []
        child = self.get_current_child()
        if child:
            ref_list += child.pick_current_refs()
        object = self.get_object()
        if object:
            ref_list += object.pick_current_refs()
        return ref_list

    def get_url(self):
        object = self.get_object()
        if object:
            return object.get_url()
        child = self.get_current_child()
        if child:
            return child.get_url()
        return None

    def get_object(self):
        return None

    def object_selected(self, obj):
        return self._parent().object_selected(obj)

    def open(self, handle):
        self._parent().open(handle)

    def hide_me(self):
        self._parent().hide_current()

    def replace_view(self, mapper):
        return mapper(self.handle())

    def get_global_commands(self):
        return self._parent().get_global_commands()

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

    def hide_current(self):
        self._parent().hide_current()

    def print_key_event(self, evt, prefix):
        print_key_event(evt, '%s %s %s' % (prefix, self._cls2name(self), hex(id(self))))

    def _cls2name(self, cls):
        return cls.__module__ + '.' + cls.__class__.__name__

    def pick_arg(self, kind):
        return self._parent().pick_arg(kind)
