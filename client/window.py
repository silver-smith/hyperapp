import weakref
from PySide import QtCore, QtGui
from util import DEBUG_FOCUS, call_after
from view_command import command
import view
import composite
from menu_bar import MenuBar
import cmd_pane
#import filter_pane


DEFAULT_SIZE = QtCore.QSize(800, 800)
DUP_OFFSET = QtCore.QPoint(150, 50)


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

    @command('Duplicate window', 'Duplicate window', 'Alt+W')
    def duplicate_window( self ):
        self.handle().move(DUP_OFFSET).construct(self._parent())

    def __del__( self ):
        print '~window'
