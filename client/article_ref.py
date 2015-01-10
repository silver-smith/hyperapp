from PySide import QtCore, QtGui
from util import uni2str
from iface import ObjectIface
import iface_registry
import view
import view_registry


class ArticleRef(ObjectIface):

    def __init__( self, server, response ):
        ObjectIface.__init__(self, server, response)
        self.article_id = response['article_id']
        self.path = response['path']


class Handle(view.Handle):

    def __init__( self, object, path=None ):
        view.Handle.__init__(self)
        self.object = object
        self.path = path

    def get_title( self ):
        return self.object.get_title()

    def construct( self, parent ):
        print 'article_ref construct', parent, self.object.get_title(), repr(self.path)
        return View(parent, self.object, self.path)

    def __repr__( self ):
        return 'text_edit.Handle(%s, %s)' % (uni2str(self.object.get_title()), uni2str(self.path))


class View(view.View, QtGui.QWidget):

    def __init__( self, parent, object, path ):
        QtGui.QWidget.__init__(self)
        view.View.__init__(self, parent)
        self.object = object
        self.article_id_label = QtGui.QLabel('Article#%d' % self.object.article_id)
        self.path_line_edit = QtGui.QLineEdit()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.article_id_label)
        layout.addWidget(self.path_line_edit)
        self.setLayout(layout)

    def handle( self ):
        return Handle(self.object, '')

    def get_title( self ):
        return self.object.get_title()

    def get_object( self ):
        return self.object

    def get_widget_to_focus( self ):
        return self.path_line_edit


iface_registry.register_iface('article_ref', ArticleRef)
view_registry.register_view('article_ref', Handle)
