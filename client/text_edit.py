from PySide import QtCore, QtGui
from util import uni2str
import view
import view_registry


class Handle(view.Handle):

    def __init__( self, object, text=None ):
        view.Handle.__init__(self)
        self.object = object
        self.text = text

    def title( self ):
        return self.object.title()

    def construct( self, parent ):
        print 'text_edit construct', parent, self.object.title(), repr(self.text)
        return View(parent, self.object, self.text)

    def __repr__( self ):
        return 'text_edit.Handle(%s, %s)' % (uni2str(self.object.title()), uni2str(self.text))


class View(view.View, QtGui.QTextEdit):

    def __init__( self, parent, object, text ):
        QtGui.QTextEdit.__init__(self, text)
        view.View.__init__(self, parent)
        self.object = object

    def handle( self ):
        return Handle(self.object, self.toPlainText())

    def title( self ):
        return self.object.title()

    def get_object( self ):
        return self.object


view_registry.register_view('text', Handle)
