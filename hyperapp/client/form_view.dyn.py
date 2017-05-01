import logging
import asyncio
from PySide import QtCore, QtGui
from ..common.interface.form import string_field_handle, int_field_handle, form_field, form_handle
from .util import call_after
from .command import command
from . import view

log = logging.getLogger(__name__)


def register_views(registry, services):
    registry.register(View.view_id, View.from_state, services.objimpl_registry)


class LineEditField(view.View, QtGui.QLineEdit):

    @classmethod
    def from_state(cls, state, parent):
        return cls(parent, state.value)

    def __init__(self, parent, value):
        QtGui.QLineEdit.__init__(self, value)
        view.View.__init__(self, parent)

    def get_state(self):
        return self.handle_type(self.field_view_id, self.get_value())

    def ensure_has_focus(self):
        view.View.ensure_has_focus(self)
        self.selectAll()


class StringField(LineEditField):

    field_view_id = 'string'
    handle_type = string_field_handle

    def get_value(self):
        return self.text()

    def __del__(self):
        log.info('~string_field')


class IntField(LineEditField):

    field_view_id = 'int'
    handle_type = int_field_handle

    def __init__(self, parent, value):
        # todo: input mask
        LineEditField.__init__(self, parent, str(value))

    def get_value(self):
        return int(self.text())

    def __del__(self):
        log.info('~int_field')


class View(view.View, QtGui.QWidget):

    view_id = 'form'

    @classmethod
    @asyncio.coroutine
    def from_state(cls, locale, state, parent, objimpl_registry):
        object = objimpl_registry.resolve(state.object)
        return cls(parent, object, state.fields, state.current_field)

    def __init__(self, parent, object, fields, current_field):
        QtGui.QWidget.__init__(self)
        view.View.__init__(self, parent)
        self.object = object
        self.fields = []  # (name, field_view) list
        layout = QtGui.QVBoxLayout()
        for idx, field in enumerate(fields):
            self._construct_field(layout, field.name, field.field_handle, focus_it = idx==current_field)
        layout.addStretch()
        self.setLayout(layout)
        self.object.subscribe(self)

    def _construct_field(self, layout, name, field_state, focus_it):
        field_view = field_registry.resolve(field_state, self)
        self.fields.append((name, field_view))
        label = QtGui.QLabel(name)
        label.setBuddy(field_view)
        layout.addWidget(label)
        layout.addWidget(field_view)
        layout.addSpacing(10)
        if focus_it:
            call_after(field_view.ensure_has_focus)

    def get_state(self):
        fields = []
        focused_idx = None
        for idx, (name, field) in enumerate(self.fields):
            if field.has_focus():
                focused_idx = idx
            fields.append(form_field(name, field.get_state()))
        return form_handle(self.view_id, self.object.get_state(), fields, focused_idx)

    def get_object(self):
        return self.object

    def get_widget_to_focus(self):
        return self.fields[0][1].get_widget()

    @command('submit')  # 'Submit', 'Submit form', 'Return')
    @asyncio.coroutine
    def command_submit(self):
        field_values = {}
        for name, field in self.fields:
            field_values[name] = field.get_value()
        handle = yield from self.object.run_command('submit', **field_values)
        if handle:
            self.open(handle)


class FieldRegistry(object):

    def __init__(self):
        self.registry = {}  # field view id -> field ctr

    def register(self, field_view_id, ctr):
        assert field_view_id not in self.registry, repr(field_view_id)  # Duplicate id
        self.registry[field_view_id] = ctr

    def resolve(self, state, parent):
        return self.registry[state.field_view_id](state, parent)


field_registry = FieldRegistry()

field_registry.register(StringField.field_view_id, StringField.from_state)
field_registry.register(IntField.field_view_id, IntField.from_state)
