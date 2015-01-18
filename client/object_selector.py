from PySide import QtCore, QtGui
from util import uni2str
from iface import ObjectIface
import iface_registry
import view
import view_registry


class ObjectSelector(ObjectIface):

    def __init__( self, server, response ):
        ObjectIface.__init__(self, server, response)
        self.target = server.resp2object(response['target'])
        self.target_view_id = response['target']['view_id']

    ## def get_title( self ):
    ##     return '%s -> %s' % (self.path, self.target.path)

    def get_target( self ):
        return self.target

    def set_target( self, object ):
        self.target = object

    def get_target_handle( self ):
        handle_ctr = view_registry.resolve_view(self.target_view_id)
        return handle_ctr(self.target)


class Handle(view.Handle):

    def __init__( self, object ):
        view.Handle.__init__(self)
        self.object = object

    def get_title( self ):
        return self.object.get_title()

    def construct( self, parent ):
        print 'object selector construct', parent, self.object.get_title(), self.object.target.get_title()
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
        self.target_view.get_widget().deleteLater()  # just removing it from layout won't destroy it
        self.target_view = handle.construct(self)
        self.object.set_target(self.target_view.get_object())
        self.groupBox.layout().addWidget(self.target_view)
        self.view_changed()

    def get_widget_to_focus( self ):
        return self.target_view.get_widget_to_focus()

    def __del__( self ):
        print '~object_selector.View'


iface_registry.register_iface('object_selector', ObjectSelector)
view_registry.register_view('object_selector', Handle)
