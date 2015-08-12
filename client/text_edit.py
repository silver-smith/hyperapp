from PySide import QtCore, QtGui
from .util import uni2str
from .view_registry import view_registry
from . import view
from .text_object import TextObject


class Handle(view.Handle):

    @classmethod
    def decode( cls, server, contents ):
        return cls(server.resolve_object(contents.object))

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


class View(view.View, QtGui.QTextEdit):

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

    def get_object_commands( self ):
        return (self, self.object.get_commands(TextObject.mode_edit))

    def _on_text_changed( self ):
        if self.notify_on_text_changed:
            self.object.text_changed(self.toPlainText(), emitter_view=self)

    # todo: preserve cursor position
    def object_changed( self ):
        self.notify_on_text_changed = False
        try:
            self.setPlainText(self.object.text)
        finally:
            self.notify_on_text_changed = True
        view.View.object_changed(self)

    def __del__( self ):
        print '~text_edit', self


TextObject.set_edit_handle_ctr(Handle)
view_registry.register('text_edit', Handle.decode)
