# line edit component / widget

import logging
from enum import Enum
from PySide import QtCore, QtGui

from hyperapp.client.object import Object
from hyperapp.client.module import ClientModule
from . import htypes
from .view import View

log = logging.getLogger(__name__)


class LineObject(Object):

    impl_id = 'line'

    @classmethod
    def from_state(cls, state):
        return cls(state.line)

    def __init__(self, line):
        self._line = line
        super().__init__()

    def get_title(self):
        return 'Line'

    def get_state(self):
        return htypes.line_object.line_object(self.impl_id, self._line)

    @property
    def line(self):
        return self._line

    @line.setter
    def line(self, line):
        self._line = line
        self._notify_object_changed()

    def line_changed(self, new_line, emitter_view=None):
        log.debug('line_object.line_changed: %r', new_line)
        self._line = new_line
        self._notify_object_changed(emitter_view)

    def __del__(self):
        log.info('~line_object %r', self)


class LineEditView(View, QtGui.QLineEdit):

    impl_id = 'line_edit'

    class Mode(Enum):
        VIEW = 'view'
        EDIT = 'edit'

    @classmethod
    async def from_state(cls, locale, state, parent, objimpl_registry):
        object = await objimpl_registry.resolve_async(state.object)
        return cls(object, cls.Mode(state.mode), parent)

    def __init__(self, object, mode, parent):
        QtGui.QLineEdit.__init__(self, object.line)
        View.__init__(self, parent)
        self._object = object
        self._mode = mode
        self._notify_on_line_changed = True
        self.setReadOnly(self._mode == self.Mode.VIEW)
        self.textChanged.connect(self._on_line_changed)
        self._object.subscribe(self)

    def get_state(self):
        return htypes.line_object.line_edit_view(self.impl_id, self._object.get_state(), self._mode.value)

    def get_object(self):
        return self._object

    def _on_line_changed(self, line):
        log.debug('line_edit.on_line_changed: %r', line)
        if self._notify_on_line_changed:
            self._object.line_changed(line, emitter_view=self)

    # todo: preserve cursor position
    def object_changed(self):
        self._notify_on_line_changed = False
        try:
            self.setText(self._object.line)
        finally:
            self._notify_on_line_changed = True
        View.object_changed(self)

    def __del__(self):
        log.info('~line_edit')


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.objimpl_registry.register(LineObject.impl_id, LineObject.from_state)
        services.view_registry.register(LineEditView.impl_id, LineEditView.from_state, services.objimpl_registry)
