from PySide import QtCore, QtGui
from common.interface import tStringFieldHandle, tIntFieldHandle, tFormHandle, FormField
from util import uni2str
import view


class StringFieldHandle(view.Handle):

    def __init__( self, value ):
        assert isinstance(value, basestring), repr(value)
        self.value = value

    def construct( self, parent ):
        return StringField(parent, self.value)


class IntFieldHandle(view.Handle):

    def __init__( self, value ):
        assert isinstance(value, (int, long)), repr(value)
        self.value = value

    def construct( self, parent ):
        return IntField(parent, self.value)


class StringField(view.View, QtGui.QLineEdit):

    def __init__( self, parent, value ):
        QtGui.QLineEdit.__init__(self, value)
        view.View.__init__(self, parent)

    def handle( self ):
        return StringFieldHandle(self.text())

    def __del__( self ):
        print '~string_field'


class IntField(view.View, QtGui.QLineEdit):

    def __init__( self, parent, value ):
        # todo: input mask
        QtGui.QLineEdit.__init__(self, str(value))
        view.View.__init__(self, parent)

    def handle( self ):
        return IntFieldHandle(int(self.text()))

    def __del__( self ):
        print '~int_field'


class Handle(view.Handle):

    def __init__( self, object, fields ):
        self.object = object
        self.fields = fields

    def get_object( self ):
        return self.object

    def construct( self, parent ):
        return View(parent, self.object, self.fields)

    def __repr__( self ):
        return 'form.Handle(%s, %s)' % (uni2str(self.object.get_title()), self.fields)


class View(view.View, QtGui.QWidget):

    def __init__( self, parent, object, fields ):
        QtGui.QWidget.__init__(self)
        view.View.__init__(self, parent)
        self.object = object
        self.fields = []
        layout = QtGui.QVBoxLayout()
        for field in fields:
            self._construct_field(layout, field.name, field.handle)
        layout.addStretch()
        self.setLayout(layout)

    def _construct_field( self, layout, name, field_handle ):
        field_view = field_handle.construct(self)
        self.fields.append((name, field_view))
        label = QtGui.QLabel(name)
        label.setBuddy(field_view)
        layout.addWidget(label)
        layout.addWidget(field_view)
        layout.addSpacing(10)

    def get_current_child( self ):
        return self.fields[0][1]

    def handle( self ):
        return Handle(self.object, [FormField(name, field.handle()) for name, field in self.fields])


tStringFieldHandle.register_class(StringFieldHandle)
tIntFieldHandle.register_class(IntFieldHandle)
tFormHandle.register_class(Handle)
