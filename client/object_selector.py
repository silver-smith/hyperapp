from PySide import QtCore, QtGui
from util import uni2str
from server import resolve_object
from command import ObjectCommand
from proxy_object import ProxyObject
import iface_registry
import view
import view_registry


class ObjectSelector(ProxyObject):

    @classmethod
    def from_resp( cls, server, resp ):
        path, commands = ProxyObject.parse_resp(resp)
        handle = resolve_object(server, resp['target'])
        return cls(server, path, commands, handle)

    def __init__( self, server, path, commands, target_handle ):
        ProxyObject.__init__(self, server, path, commands)
        self.target_object = target_handle.get_object()
        self.target_handle = target_handle

    ## def get_title( self ):
    ##     return '%s -> %s' % (self.path, self.target.path)

    def get_commands( self ):
        return [ObjectCommand('choose', 'Choose', 'Choose current object', 'Ctrl+Return')] \
          + self.target_object.get_commands()

    def run_command( self, command_id ):
        if command_id == 'choose':
            return self.run_command_choose()
        return self.target_object.run_command(command_id)

    def run_command_choose( self ):
        if not isinstance(self.target_object, ProxyObject): return  # not a proxy - can not choose it
        request = dict(self.make_command_request(command_id='choose'),
                       target_path=self.target_object.path)
        response = self.server.execute_request(request)
        return UnwrapHandle(response.object())

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
        print 'object_selector construct', parent, self.object.get_title(), self.object.target_object.get_title()
        return View(parent, self.object)

    def __repr__( self ):
        return 'object_selector.Handle(%s)' % uni2str(self.object.get_title())


class UnwrapHandle(view.Handle):

    def __init__( self, base_handle ):
        assert isinstance(base_handle, view.Handle), repr(base_handle)
        view.Handle.__init__(self)
        self.base_handle = base_handle

    def get_object( self ):
        return self.base_handle.get_object()

    def construct( self, parent ):
        print 'object_selector.UnwrapHandle construct', parent, self.base_handle
        return self.base_handle.construct(parent)

    def __repr__( self ):
        return 'object_selector.UnwrapHandle(%r)' % self.base_handle


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

    def get_object( self ):
        return self.object

    def current_child( self ):
        return self.target_view

    def open( self, handle ):
        print 'object_selector open', handle
        if not isinstance(handle, UnwrapHandle):
            new_object = self.object.with_another_handle(handle)
            handle = Handle(new_object)
        view.View.open(self, handle)

    def __del__( self ):
        print '~object_selector.View'


iface_registry.register_iface('object_selector', ObjectSelector.from_resp)
view_registry.register_view('object_selector', Handle)
