import logging
import re
from PySide import QtCore, QtGui
from ..common.htypes import tString, tObject, Field, tObjHandle
from .util import uni2str
from .objimpl_registry import objimpl_registry
from .view_registry import view_registry
from . import view
from .text_object import TextObject

log = logging.getLogger(__name__)


dataType = tObjHandle


class Handle(view.Handle):

    @classmethod
    def from_data( cls, contents, server=None ):
        object = objimpl_registry.produce_obj(contents.object, server)
        return cls(object)

    def __init__( self, object ):
        view.Handle.__init__(self)
        self.object = object

    def to_data( self ):
        return dataType('text_view', self.object.to_data())

    def get_object( self ):
        return self.object

    def construct( self, parent ):
        log.info('text_view construct parent=%r object=%r title=%r', parent, self.object, self.object.get_title())
        return View(parent, self.object)

    def __repr__( self ):
        return 'text_view.Handle(%s)' % uni2str(self.object.get_title())


class View(view.View, QtGui.QTextBrowser):

    def __init__( self, parent, object ):
        QtGui.QTextBrowser.__init__(self)
        view.View.__init__(self, parent)
        self.setOpenLinks(False)
        self.object = object
        self.setHtml(self.text2html(object.text or ''))
        self.anchorClicked.connect(self.on_anchor_clicked)
        self.object.subscribe(self)

    def handle( self ):
        return Handle(self.object)

    def get_title( self ):
        return self.object.get_title()

    def get_object( self ):
        return self.object

    def get_object_commands( self ):
        return view.View.get_object_commands(self, TextObject.mode_view)

    def text2html( self, text ):
        return re.sub(r'\[([^\]]+)\]', r'<a href="\1">\1</a>', text or '')

    def on_anchor_clicked( self, url ):
        log.info('on_anchor_clicked url.path=%r', url.path())
        self.object.open_ref(self, url.path())

    def object_changed( self ):
        self.setHtml(self.text2html(self.object.text))
        view.View.object_changed(self)

    def __del__( self ):
        log.info('~text_view %r', self)


TextObject.set_view_handle_ctr(Handle)
view_registry.register('text_view', Handle.from_data)
