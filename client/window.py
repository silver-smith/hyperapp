import weakref
import uuid
from PySide import QtCore, QtGui
from common.util import is_list_inst
from util import DEBUG_FOCUS, call_after, make_action
from common.interface import Interface
from common.request import Request
import proxy_registry
from view_command import ViewCommandBase, command
import view
import composite
from menu_bar import MenuBar
import cmd_pane
#import filter_pane


DEFAULT_SIZE = QtCore.QSize(800, 800)
DUP_OFFSET = QtCore.QPoint(150, 50)


class OpenRespHandler(proxy_registry.RespHandler):

    def __init__( self, iface, command_id, window ):
        proxy_registry.RespHandler.__init__(self, iface, command_id)
        self.window_wref = weakref.ref(window)

    def process_response( self, response ):
        window = self.window_wref()
        if not window: return
        window.process_open_command_response(self, response.result)


class OpenCommand(ViewCommandBase):

    def __init__( self, id, text, desc, shortcut, iface, path ):
        assert isinstance(iface, Interface), repr(iface)
        ViewCommandBase.__init__(self, text, desc, shortcut)
        self.id = id
        self.iface = iface
        self.path = path

    def run( self, window_wr ):
        print 'OpenCommand.run', self.id, self.iface, self.path, window_wr
        window = window_wr()
        if window:
            window.run_open_command(self.iface, self.path)

    def make_action( self, widget, window ):
        return make_action(widget, self.text, self.shortcut, self.run, weakref.ref(window))


class Handle(composite.Handle):

    def __init__( self, child_handle, size=None, pos=None ):
        composite.Handle.__init__(self)
        self.child_handle = child_handle
        self.size = size
        self.pos = pos

    def get_child_handle( self ):
        return self.child_handle

    def construct( self, app ):
        print 'window construct', app, self.child_handle
        return Window(app, self.child_handle, self.size, self.pos)

    def move( self, point ):
        return Handle(self.child_handle, self.size, self.pos + point)


class Window(composite.Composite, QtGui.QMainWindow):

    def __init__( self, app, child_handle, size=None, pos=None ):
        QtGui.QMainWindow.__init__(self)
        composite.Composite.__init__(self, app)
        self._app = app  # alias for _parent()
        self._view = None
        self._child_widget = None
        if size:
            self.resize(size)
        else:
            self.resize(DEFAULT_SIZE)
        if pos:
            self.move(pos)
        else:
            self.move(800, 100)
        self._menu_bar = MenuBar(app, weakref.ref(self))
        self._cmd_pane = cmd_pane.View(self)
        #self._filter_pane = filter_pane.View(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._cmd_pane)
        #self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._filter_pane)
        self.resp_handlers = set()  # explicit refs to OpenRespHandler to keep them alive until window is alive
        self.set_child(child_handle)
        self.show()
        self._parent().window_created(self)

    def closeEvent( self, evt ):
        QtGui.QMainWindow.closeEvent(self, evt)
        ## self.deleteLater()  # seems not required, at least when moved to QMainWindow from QWidget
        self._parent().window_closed(self)

    def handle( self ):
        return Handle(self._view.handle(), self.size(), self.pos())

    def get_current_child( self ):
        return self._view

    def replace_view( self, mapper ):
        handle = mapper(self._view.handle())
        if handle:
            self.set_child(handle)

    def set_child( self, handle ):
        self._view = handle.construct(self)
        self.view_changed(self._view)

    def open( self, handle ):
        self._view.open(handle)

    def selected_elements_changed( self, elts ):
        call_after(self._menu_bar.selected_elements_changed, elts)
        self._cmd_pane.selected_elements_changed(elts)
        #self._filter_pane.selected_elements_changed(elts)

    def object_selected( self, obj ):
        return False

    def view_changed( self, view ):
        assert view is self._view
        w = self._view.get_widget()
        if w is not self._child_widget:
            if DEBUG_FOCUS: print '*** window.view_changed: replacing widget', self, view, w, 'old w:', self._child_widget
            if self._child_widget:
                self._child_widget.deleteLater()
            self.setCentralWidget(w)
            self._child_widget = w
        self.setWindowTitle(view.get_title())
        self._menu_bar.view_changed(self)
        self._cmd_pane.view_changed(self)
        #self._filter_pane.view_changed(self)

    def run_open_command( self, iface, path ):
        command_id = 'get'
        #iface.validate_request(command_id)
        resp_handler = OpenRespHandler(iface, command_id, self)
        request_id = str(uuid.uuid4())
        request = Request(self._app.server, iface, path, command_id, request_id)
        self._app.server.execute_request(request, resp_handler)
        self.resp_handlers.add(resp_handler)

    def process_open_command_response( self, resp_handler, handle ):
        self.resp_handlers.remove(resp_handler)
        self.get_current_view().open(handle)

    @command('Duplicate window', 'Duplicate window', 'Alt+W')
    def duplicate_window( self ):
        self.handle().move(DUP_OFFSET).construct(self._parent())

    def __del__( self ):
        print '~window'
