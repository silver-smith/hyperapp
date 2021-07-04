# line edit component / widget

import logging
from enum import Enum

from PySide2 import QtCore, QtWidgets

from hyperapp.common.module import Module

from . import htypes
from .object import Object
from .view import View
from .string_object import StringObject

log = logging.getLogger(__name__)


class LineEditView(View, QtWidgets.QLineEdit):

    @classmethod
    async def from_piece(cls, piece, object):
        return cls(object, piece.editable)

    def __init__(self, object, editable):
        QtWidgets.QLineEdit.__init__(self, object.value)
        View.__init__(self)
        self._object = object
        self._editable = editable
        self._notify_on_line_changed = True
        self.setReadOnly(not self._editable)
        self.textChanged.connect(self._on_line_changed)
        self._object.subscribe(self)

    @property
    def piece(self):
        return htypes.line_edit.line_edit_view(self._editable)

    @property
    def object(self):
        return self._object

    @property
    def state(self):
        return None

    def _on_line_changed(self, line):
        log.debug('line_edit.on_line_changed: %r', line)
        if self._notify_on_line_changed:
            self._object.line_changed(line, emitter_view=self)

    # todo: preserve cursor position
    def object_changed(self):
        self._notify_on_line_changed = False
        try:
            self.setText(self._object.value)
        finally:
            self._notify_on_line_changed = True
        View.object_changed(self)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.lcs.add([htypes.view.available_view_d(), *StringObject.dir_list[-1]], htypes.line_edit.line_edit_view(editable=False))
        services.lcs.add([htypes.view.available_view_d(), *StringObject.dir_list[-1]], htypes.line_edit.line_edit_view(editable=True))
        services.view_registry.register_actor(htypes.line_edit.line_edit_view, LineEditView.from_piece)
