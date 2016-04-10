from PySide import QtCore, QtGui
from ..common.util import is_list_inst
from ..common.interface.form import tStringFieldHandle, tIntFieldHandle, tFormField, tFormHandle
from .util import uni2str, call_after
from .objimpl_registry import objimpl_registry
from .view_registry import view_registry
from . import view


class FieldHandle(object):

    @classmethod
    def from_data( cls, contents ):
        return cls(contents.value)

    def to_data( self ):
        return self.handle_type.instantiate(self.field_view_id, self.value)


class StringFieldHandle(FieldHandle):

    field_view_id = 'string'
    handle_type = tStringFieldHandle

    def __init__( self, value ):
        assert isinstance(value, basestring), repr(value)
        self.value = value

    def construct( self, parent ):
        return StringField(parent, self.value)


class IntFieldHandle(FieldHandle):

    field_view_id = 'int'
    handle_type = tIntFieldHandle

    def __init__( self, value ):
        assert isinstance(value, (int, long)), repr(value)
        self.value = value

    def construct( self, parent ):
        return IntField(parent, self.value)


class LineEditField(view.View, QtGui.QLineEdit):

    def __init__( self, parent, value ):
        QtGui.QLineEdit.__init__(self, value)
        view.View.__init__(self, parent)

    def ensure_has_focus( self ):
        view.View.ensure_has_focus(self)
        self.selectAll()


class StringField(LineEditField):

    def handle( self ):
        return StringFieldHandle(self.get_value())

    def get_value( self ):
        return self.text()

    def __del__( self ):
        print '~string_field'


class IntField(LineEditField):

    def __init__( self, parent, value ):
        # todo: input mask
        LineEditField.__init__(self, parent, str(value))

    def handle( self ):
        return IntFieldHandle(self.get_value())

    def get_value( self ):
        return int(self.text())

    def __del__( self ):
        print '~int_field'


class Field(object):

    @classmethod
    def from_data( cls, rec ):
        return cls(rec.name, field_registry.resolve(rec.field_handle))

    def __init__( self, name, field_handle ):
        assert isinstance(field_handle, FieldHandle), repr(field_handle)  # invalid value resolved from registry 
        self.name = name
        self.handle = field_handle

    def to_data( self ):
        return tFormField.instantiate(self.name, self.handle.to_data())


class Handle(view.Handle):

    view_id = 'form'

    @classmethod
    def from_data( cls, contents, server=None ):
        object = objimpl_registry.produce_obj(contents.object, server)
        fields = [Field.from_data(rec) for rec in contents.fields] 
        return cls(object, fields, contents.current_field)

    def __init__( self, object, fields, current_field=0 ):
        assert is_list_inst(fields, Field), repr(fields)
        self.object = object
        self.fields = fields
        self.current_field = current_field

    def to_data( self ):
        return tFormHandle.instantiate(
            self.view_id, self.object.to_data(), [field.to_data() for field in self.fields], self.current_field)

    def get_object( self ):
        return self.object

    def construct( self, parent ):
        print 'form construct', parent, self.object.get_title(), self.current_field, self.fields
        return View(parent, self.object, self.fields, self.current_field)

    def __repr__( self ):
        return 'form.Handle(%s, %s)' % (uni2str(self.object.get_title()), self.fields)


class View(view.View, QtGui.QWidget):

    def __init__( self, parent, object, fields, current_field ):
        QtGui.QWidget.__init__(self)
        view.View.__init__(self, parent)
        self.object = object
        self.fields = []  # (name, field_view) list
        layout = QtGui.QVBoxLayout()
        for idx, field in enumerate(fields):
            self._construct_field(layout, field.name, field.handle, focus_it=idx == current_field)
        layout.addStretch()
        self.setLayout(layout)
        self.object.subscribe(self)

    def _construct_field( self, layout, name, field_handle, focus_it ):
        field_view = field_handle.construct(self)
        self.fields.append((name, field_view))
        label = QtGui.QLabel(name)
        label.setBuddy(field_view)
        layout.addWidget(label)
        layout.addWidget(field_view)
        layout.addSpacing(10)
        if focus_it:
            call_after(field_view.ensure_has_focus)

    def get_object( self ):
        return self.object

    def get_widget_to_focus( self ):
        return self.fields[0][1].get_widget()

    def handle( self ):
        fields = []
        focused_idx = None
        for idx, (name, field) in enumerate(self.fields):
            if field.has_focus():
                focused_idx = idx
            fields.append(Field(name, field.handle()))
        return Handle(self.object, fields, focused_idx)

    def run_object_command( self, command_id ):
        if command_id == 'submit':
            self.run_object_command_submit(command_id)
        else:
            view.View.run_object_command(self, command_id)

    def run_object_command_submit( self, command_id ):
        field_values = {}
        for name, field in self.fields:
            field_values[name] = field.get_value()
        handle = self.object.run_command(command_id, self, **field_values)
        if handle:  # command is handled by client-side
            self.open(handle)



class FieldRegistry(object):

    def __init__( self ):
        self.registry = {}  # field view id -> Handle ctr

    def register( self, field_view_id, handle_ctr ):
        assert field_view_id not in self.registry, repr(field_view_id)  # Duplicate id
        self.registry[field_view_id] = handle_ctr

    def resolve( self, contents ):
        return self.registry[contents.field_view_id](contents)


field_registry = FieldRegistry()

field_registry.register(StringFieldHandle.field_view_id, StringFieldHandle.from_data)
field_registry.register(IntFieldHandle.field_view_id, IntFieldHandle.from_data)
view_registry.register(Handle.view_id, Handle.from_data)
