# line edit component / widget

import logging
from PySide import QtCore, QtGui

from ..common.interface import line_object as line_object_types
from .module import Module
from .object import Object
from . import view

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
        return line_object_types.line_object(self.impl_id, self._line)

    @property
    def line(self):
        return self._line

    def line_changed(self, new_line, emitter_view=None):
        log.debug('line_object.line_changed: %r', new_line)
        self._line = new_line
        self._notify_object_changed(emitter_view)

    def __del__(self):
        log.info('~line_object %r', self)


class LineEditView(view.View, QtGui.QLineEdit):

    impl_id = 'line_edit'

    @classmethod
    async def from_state(cls, locale, state, parent, objimpl_registry):
        object = await objimpl_registry.resolve(state.object)
        return cls(object, parent)

    def __init__(self, object, parent):
        QtGui.QLineEdit.__init__(self, object.line)
        view.View.__init__(self, parent)
        self._object = object
        self._notify_on_line_changed = True
        self.textChanged.connect(self._on_line_changed)

    def get_state(self):
        return line_object_types.line_edit_view(self.impl_id, self._object.get_state())

    def _on_line_changed(self, line):
        log.debug('line_edit.on_line_changed: %r', line)
        if self._notify_on_line_changed:
            self._object.line_changed(line, emitter_view=self)

    # todo: preserve cursor position
    def object_changed(self):
        self._notify_on_line_changed = False
        try:
            self.setText(self.object.line)
        finally:
            self._notify_on_line_changed = True
        view.View.object_changed(self)

    def __del__(self):
        log.info('~line_edit')


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(services)
        services.objimpl_registry.register(LineObject.impl_id, LineObject.from_state)
        services.view_registry.register(LineEditView.impl_id, LineEditView.from_state, services.objimpl_registry)
