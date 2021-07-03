# line edit component / widget

import logging
from enum import Enum
from PySide2 import QtCore, QtWidgets

from . import htypes
from .object import Object
from .view import View
from .command import command
from .module import ClientModule

log = logging.getLogger(__name__)


class LineEditView(View, QtWidgets.QLineEdit):

    def __init__(self, object, editable):
        QtWidgets.QLineEdit.__init__(self, object.value)
        View.__init__(self)
        self._object = object
        self._editable = editable
        self._notify_on_line_changed = True
        self.setReadOnly(not self._editable)
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

    # def __del__(self):
    #     log.info('~line_edit')


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._mosaic = services.mosaic
        # services.available_object_layouts.register('line', [htypes.string_ot.string_ot], self._make_line_layout_data)
        # services.default_object_layouts.register('line', [htypes.string_ot.string_ot], self._make_line_layout_data)
    #     services.object_layout_registry.register_actor(
    #         htypes.line.line_edit_layout, LineEditLayout.from_data, services.mosaic, services.async_web)

    # async def _make_line_layout_data(self, object_type):
    #     object_type_ref = self._mosaic.put(object_type)
    #     command_list = ObjectLayout.make_default_command_list(object_type)
    #     return htypes.line.line_edit_layout(object_type_ref, command_list, editable=False)
