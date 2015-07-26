from PySide import QtCore, QtGui
from common.interface import tStringFieldHandle, tIntFieldHandle, tFormHandle
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
        return 'form.Handle(%s, %s)' % (uni2str(self.object.title()), self.fields)


class View(view.View, QtGui.QWidget):

    def __init__( self, parent, object, fields ):
        QtGui.QWidget.__init__(self)
        view.View.__init__(self, parent)
        self.object = object
        self.fields = [field.construct(self) for field in fields]
        layout = QtGui.QVBoxLayout()
        for field in self.fields:
            layout.addWidget(field)
        self.setLayout(layout)

    def get_current_child( self ):
        return self.fields[0]

    def handle( self ):
        return Handle(self.object, [field.handle() for field in self.fields])


tStringFieldHandle.register_class(StringFieldHandle)
tIntFieldHandle.register_class(IntFieldHandle)
tFormHandle.register_class(Handle)
