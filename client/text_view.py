import re
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
        print 'text_view construct', parent, self.object, self.object.get_title(), repr(self.text)
        return View(parent, self.object, self.text)

    def __repr__( self ):
        return 'text_view.Handle(%s, %s)' % (uni2str(self.object.get_title()), uni2str(self.text))


class View(view.View, QtGui.QTextBrowser, ObjectObserver):

    def __init__( self, parent, object, text ):
        QtGui.QTextBrowser.__init__(self)
        view.View.__init__(self, parent)
        self.setOpenLinks(False)
        self.object = object
        self.setHtml(self.text2html(object.text))
        self.anchorClicked.connect(self.on_anchor_clicked)
        self.object.subscribe(self)

    def handle( self ):
        return Handle(self.object, self.toPlainText())

    def get_title( self ):
        return self.object.get_title()

    def get_object( self ):
        return self.object

    def text2html( self, text ):
        return re.sub(r'\[([^\]]+)\]', r'<a href="\1">\1</a>', text)

    def on_anchor_clicked( self, url ):
        print 'on_anchor_clicked', repr(url.path())
        handle = self.object.open_ref(url.path())
        if handle:
            self.open(handle)

    # as ObjectObserver
    def object_changed( self ):
        self.setHtml(self.text2html(self.object.text))

    def __del__( self ):
        print '~text_view'


view_registry.register_view('text_view', Handle)
