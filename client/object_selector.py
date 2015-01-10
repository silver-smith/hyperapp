from PySide import QtCore, QtGui
from iface import ObjectIface
import iface_registry
import view
import view_registry


class ObjectSelector(ObjectIface):

    def __init__( self, server, response ):
        ObjectIface.__init__(self, server, response)
        self.target_path = response['target_path']
        self.target = None

    def get_title( self ):
        return '%s -> %s' % (self.path, self.target_path)

    def get_target( self ):
        pass        


class Handle(view.Handle):

    def __init__( self, object ):
        view.Handle.__init__(self)
        self.object = object

    def get_title( self ):
        return self.object.get_title()

    def construct( self, parent ):
        print 'object selector construct', parent, self.object.get_title()
        return View(parent, self.object)

    def __repr__( self ):
        return 'object_selector.Handle(%s)' % uni2str(self.object.get_title())


class View(view.View, QtGui.QWidget):

    def __init__( self, parent, object ):
        QtGui.QWidget.__init__(self)
        view.View.__init__(self, parent)
        self.object = object

    def handle( self ):
        return Handle(self.object)

    def get_title( self ):
        return self.object.get_title()

    def get_object( self ):
        return self.object


iface_registry.register_iface('object_selector', ObjectSelector)
view_registry.register_view('object_selector', Handle)
