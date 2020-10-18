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
    async def from_data(cls, state, path, layout_watcher, ref_registry, async_ref_resolver):
        object_type = await async_ref_resolver.resolve_ref_to_object(state.object_type_ref)
        return cls(ref_registry, layout_watcher, path, object_type, state.command_list, state.editable)

    def __init__(self, ref_registry, layout_watcher, path, object_type, command_list_data, editable):
        super().__init__(ref_registry, path, object_type, command_list_data)
        self._layout_watcher = layout_watcher
        self._editable = editable

    @property
    def data(self):
        return htypes.line.line_edit_layout(self._object_type_ref, self._command_list_data, self._editable)

    async def create_view(self, command_hub, object):
        return LineEditView(object, self._editable)

    async def visual_item(self):
        if self._editable:
            tag = 'editable'
            current_command = self._set_read_only
        else:
            tag = 'read-only'
            current_command = self._set_editable
        return self.make_visual_item(
            f'LineEdit/{tag}',
            current_commands=[current_command],
            all_commands=[self._set_read_only, self._set_editable],
            )

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
        self._ref_registry = services.ref_registry
        services.object_registry.register_actor(htypes.line.line, LineObject.from_state)
        services.available_object_layouts.register('line', [LineObject.type._t], self._make_line_layout_data)
        services.default_object_layouts.register('line', [LineObject.type._t], self._make_line_layout_data)
        services.object_layout_registry.register_actor(
            htypes.line.line_edit_layout, LineEditLayout.from_data, services.ref_registry, services.async_ref_resolver)

    async def _make_line_layout_data(self, object_type):
        object_type_ref = self._ref_registry.distil(object_type)
        command_list = ObjectLayout.make_default_command_list(object_type)
        return htypes.line.line_edit_layout(object_type_ref, command_list, editable=False)
