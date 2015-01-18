from PySide import QtCore, QtGui
from util import uni2str
from iface import ObjectIface
import iface_registry
import view
import view_registry


class ObjectSelector(ObjectIface):

    @classmethod
    def from_response( cls, server, response ):
        path, commands = ObjectIface.parse_response(response)
        handle = server.resp2handle(response['target'])
        return cls(server, path, commands, handle)

    def __init__( self, server, path, commands, target_handle ):
        ObjectIface.__init__(self, server, path, commands)
        self.target_object = target_handle.get_object()
        self.target_handle = target_handle

    ## def get_title( self ):
    ##     return '%s -> %s' % (self.path, self.target.path)

    def get_target( self ):
        return self.target

    def set_target( self, object ):
        self.target = object

    def get_target_handle( self ):
        return self.target_handle

    def with_another_handle( self, handle ):
        return ObjectSelector(self.server, self.path, self.commands, handle)


class Handle(view.Handle):

    def __init__( self, object ):
        assert isinstance(object, ObjectSelector), repr(object)
        view.Handle.__init__(self)
        self.object = object

    def get_object( self ):
        return self.object

    def construct( self, parent ):
        print 'object selector construct', parent, self.object.get_title(), self.object.target_object.get_title()
        return View(parent, self.object)

    def __repr__( self ):
        return 'object_selector.Handle(%s)' % uni2str(self.object.get_title())


class View(view.View, QtGui.QWidget):

    def __init__( self, parent, object ):
        QtGui.QWidget.__init__(self)
        view.View.__init__(self, parent)
        self.object = object
        self.target_view = self.object.get_target_handle().construct(self)
        self.groupBox = QtGui.QGroupBox('Select object for %s' % self.object.get_title())
        gbl = QtGui.QVBoxLayout()
        gbl.addWidget(self.target_view.get_widget())
        self.groupBox.setLayout(gbl)
        l = QtGui.QVBoxLayout()
        l.addWidget(self.groupBox)
        self.setLayout(l)

    def handle( self ):
        return Handle(self.object)

    def get_title( self ):
        return self.object.get_title()

    def current_child( self ):
        return self.target_view

    def open( self, handle ):
        print 'object_selector open', handle
        new_object = self.object.with_another_handle(handle)
        new_handle = Handle(new_object)
        view.View.open(self, new_handle)

    def __del__( self ):
        print '~object_selector.View'


iface_registry.register_iface('object_selector', ObjectSelector.from_response)
view_registry.register_view('object_selector', Handle)
