# line edit component / widget

import logging
from enum import Enum
from PySide2 import QtCore, QtWidgets

from hyperapp.client.command import command
from hyperapp.client.object import Object
from hyperapp.client.module import ClientModule

from . import htypes
from .layout_handle import UpdateVisualItemDiff
from .layout import ObjectLayout
from .view import View

log = logging.getLogger(__name__)


class LineObject(Object):

    type = htypes.line.line_object_type(command_list=())

    @classmethod
    def from_state(cls, state):
        return cls(state.line)

    def __init__(self, line):
        self._line = line
        super().__init__()

    @property
    def title(self):
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
    async def from_data(cls, state, path, object, layout_watcher):
        return cls(layout_watcher, path, object, state.command_list, state.editable)

    def __init__(self, layout_watcher, path, object, command_list_data, editable):
        super().__init__(path, object, command_list_data)
        self._layout_watcher = layout_watcher
        self._editable = editable

    @property
    def data(self):
        return htypes.line.line_edit_layout(self._command_list_data, self._editable)

    async def create_view(self, command_hub):
        return LineEditView(self._object, self._editable)

    async def visual_item(self):
        if self._editable:
            tag = 'editable'
            command = self._set_read_only
        else:
            tag = 'read-only'
            command = self._set_editable
        return self.make_visual_item(f'LineEdit/{tag}', commands=[command])

    @command('set_editable', kind='element')
    async def _set_editable(self, item_key):
        self._editable = True
        await self._distribute_update()

    @command('set_read_only', kind='element')
    async def _set_read_only(self, item_key):
        self._editable = False
        await self._distribute_update()

    async def _distribute_update(self):
        item = await self.visual_item()
        self._layout_watcher.distribute_diffs([UpdateVisualItemDiff(self._path, item)])


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(htypes.line.line, LineObject.from_state)
        services.available_object_layouts.register('line', [LineObject.type._t], self._make_line_layout_data)
        services.default_object_layouts.register('line', [LineObject.type._t], self._make_line_layout_data)
        services.object_layout_registry.register_type(htypes.line.line_edit_layout, LineEditLayout.from_data)

    async def _make_line_layout_data(self, object_type):
        command_list = ObjectLayout.make_default_command_list(object_type)
        return htypes.line.line_edit_layout(command_list, editable=False)
