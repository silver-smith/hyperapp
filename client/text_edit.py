from PySide import QtCore, QtGui
from util import uni2str
from object import ObjectObserver
import view
import view_registry


class Handle(view.Handle):

    def __init__( self, object, text=None ):
        view.Handle.__init__(self)
        self.object = object
        self.text = text

    def get_object( self ):
        return self.object

    def construct( self, parent ):
        print 'text_edit construct', parent, self.object, self.object.get_title(), repr(self.text)
        return View(parent, self.object, self.text)

    def __repr__( self ):
        return 'text_edit.Handle(%s, %s)' % (uni2str(self.object.get_title()), uni2str(self.text))


class View(view.View, QtGui.QTextEdit, ObjectObserver):

    def __init__( self, parent, object, text ):
        QtGui.QTextEdit.__init__(self, text)
        view.View.__init__(self, parent)
        self.object = object
        self.notify_on_text_changed = True
        self.setPlainText(object.text)
        self.textChanged.connect(self._on_text_changed)
        self.object.subscribe(self)

    def handle( self ):
        return Handle(self.object, self.toPlainText())

    def get_title( self ):
        return self.object.get_title()

    def get_object( self ):
        return self.object

    def _on_text_changed( self ):
        if self.notify_on_text_changed:
            self.object.text_changed(self, self.toPlainText())

    # as ObjectObserver
    # todo: preserve cursor position
    def object_changed( self ):
        self.notify_on_text_changed = False
        try:
            self.setPlainText(self.object.text)
        finally:
            self.notify_on_text_changed = True

    def __del__( self ):
        print '~text_edit'


view_registry.register_view('text_edit', Handle)
