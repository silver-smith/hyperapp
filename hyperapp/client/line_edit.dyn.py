# line edit component / widget

import logging
from enum import Enum
from PySide import QtCore, QtGui

from hyperapp.client.object import Object
from hyperapp.client.module import ClientModule
from . import htypes
from .view import View
from .view_registry import NotApplicable
from .layout_registry import LayoutViewProducer

log = logging.getLogger(__name__)


class LineObject(Object):

    @classmethod
    def from_state(cls, state):
        return cls(state.line)

    def __init__(self, line):
        self._line = line
        super().__init__()

    def get_title(self):
        return 'Line'

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

    def __init__(self, object, mode):
        QtGui.QLineEdit.__init__(self, object.line)
        View.__init__(self)
        self._object = object
        self._mode = mode
        self._notify_on_line_changed = True
        self.setReadOnly(self._mode == self.Mode.VIEW)
        self.textChanged.connect(self._on_line_changed)
        self._object.subscribe(self)

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


class LineEditProducer(LayoutViewProducer):

    def __init__(self, layout):
        pass

    async def produce_view(self, piece, object, observer=None):
        return LineEditView(object, LineEditView.Mode.EDIT)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(htypes.line.line, LineObject.from_state)
        services.view_producer_registry.register_view_producer(self._produce_view)
        services.layout_registry.register_type(htypes.line.line_edit_layout, LineEditProducer)

    async def _produce_view(self, type_ref, object, observer):
        if not isinstance(object, LineObject):
            raise NotApplicable(object)
        return LineEditView(object, LineEditView.Mode.VIEW)
