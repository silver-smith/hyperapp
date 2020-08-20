# line edit component / widget

import logging
from enum import Enum
from PySide2 import QtCore, QtWidgets

from hyperapp.client.command import command
from hyperapp.client.object import Object
from hyperapp.client.module import ClientModule

from . import htypes
from .layout import RootVisualItem, ObjectLayout
from .view import View

log = logging.getLogger(__name__)


class LineObject(Object):

    category_list = ['line']

    @classmethod
    def from_state(cls, state):
        return cls(state.line)

    def __init__(self, line):
        self._line = line
        super().__init__()

    def get_title(self):
        return 'Line'

    @property
    def data(self):
        return htypes.line.line(self.line)

    def get_value(self):
        return self._line

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

    # def __del__(self):
    #     log.info('~line_object %r', self)


class LineEditView(View, QtWidgets.QLineEdit):

    def __init__(self, object, editable):
        QtWidgets.QLineEdit.__init__(self, object.line)
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


class LineEditLayout(ObjectLayout):

    @classmethod
    async def from_data(cls, state, object):
        return cls(object, [], state.editable)

    def __init__(self, object, path, editable):
        super().__init__(path)
        self._object = object
        self._editable = editable

    @property
    def data(self):
        return htypes.line.line_edit_layout(self._editable)

    async def create_view(self, command_hub):
        return LineEditView(self._object, self._editable)

    async def visual_item(self):
        if self._editable:
            tag = 'editable'
            command = self._set_read_only
        else:
            tag = 'read-only'
            command = self._set_editable
        return RootVisualItem(f'LineEdit/{tag}', commands=[command])

    @command('set_editable')
    def _set_editable(self, item_key):
        assert 0

    @command('set_read_only')
    def _set_read_only(self, item_key):
        assert 0


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(htypes.line.line, LineObject.from_state)
        services.default_object_layouts.register('line', LineObject.category_list, self._make_line_layout_rec)
        services.available_object_layouts.register('line', LineObject.category_list, self._make_line_layout_rec)
        services.object_layout_registry.register_type(htypes.line.line_edit_layout, LineEditLayout.from_data)

    async def _make_line_layout_rec(self, object):
        return htypes.line.line_edit_layout(editable=False)
