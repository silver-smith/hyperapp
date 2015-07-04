from PySide import QtCore, QtGui
import common.interface as common_iface
import common.interface.article as article_iface
from util import uni2str
from proxy_object import ProxyObject
import proxy_registry
import view
import view_registry
from command import Command


class ObjSelectorUnwrap(article_iface.ObjSelectorUnwrap, view.Handle):

    def get_object( self ):
        return self.base_handle.get_object()

    def construct( self, parent ):
        return self.base_handle.construct(parent)


class Handle(view.Handle):

    def __init__( self, ref, target ):
        assert isinstance(ref, ProxyObject), repr(ref)
        assert isinstance(target, view.Handle), repr(target)
        view.Handle.__init__(self)
        self.ref = ref
        self.target = target

    def get_object( self ):
        return self.ref

    def construct( self, parent ):
        print 'object_selector construct', parent, self.ref.get_title(), self.target.get_object().get_title()
        return View(parent, self.ref, self.target)

    def __repr__( self ):
        return 'object_selector.Handle(%s)' % uni2str(self.ref.get_title())


class View(view.View, QtGui.QWidget):

    def __init__( self, parent, ref, target ):
        QtGui.QWidget.__init__(self)
        view.View.__init__(self, parent)
        self.ref = ref
        self.target_view = target.construct(self)
        self.groupBox = QtGui.QGroupBox('Select object for %s' % self.ref.get_title())
        gbl = QtGui.QVBoxLayout()
        gbl.addWidget(self.target_view.get_widget())
        self.groupBox.setLayout(gbl)
        l = QtGui.QVBoxLayout()
        l.addWidget(self.groupBox)
        self.setLayout(l)

    def handle( self ):
        return Handle(self.ref, self.target_view.handle())

    def get_current_child( self ):
        return self.target_view

    def get_object( self ):
        return self.ref

    def get_object_commands( self ):
        view, commands = self.target_view.get_object_commands()
        choose_cmd = Command('choose', 'Choose', 'Choose current object', 'Ctrl+Return')
        return (self, [choose_cmd] + commands)

    def run_object_command( self, command_id ):
        if command_id == 'choose':
            self.run_object_command_choose(command_id)
        else:
            self.target_view.run_object_command(command_id)

    def run_object_command_choose( self, command_id ):
        target_obj = self.target_view.get_object()
        if not isinstance(target_obj, ProxyObject): return  # not a proxy - can not choose it
        handle = self.ref.run_command(command_id, self, target_path=target_obj.path)
        if handle:  # command is handled by client-side
            self.open(handle)

    def open( self, handle ):
        if not isinstance(handle, ObjSelectorUnwrap):
            handle = Handle(self.ref, handle)
        view.View.open(self, handle)

    def __del__( self ):
        print '~object_selector.View'


proxy_registry.register_iface('object_selector', ProxyObject.from_response)
common_iface.Handle.register('object_selector', Handle)
common_iface.Handle.register('object_selector_unwrap', ObjSelectorUnwrap)
