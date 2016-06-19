import logging
import asyncio
import re
from PySide import QtCore, QtGui
from ..common.htypes import tString, tObject, Field, tObjHandle
from .objimpl_registry import objimpl_registry
from .view_registry import view_registry
from . import view
from .text_object import TextObject

log = logging.getLogger(__name__)


state_type = tObjHandle


class View(view.View, QtGui.QTextBrowser):

    @classmethod
    @asyncio.coroutine
    def from_state( cls, state, parent ):
        object = objimpl_registry.produce_obj(state.object)
        return cls(object, parent)

    def __init__( self, object, parent ):
        QtGui.QTextBrowser.__init__(self)
        view.View.__init__(self, parent)
        self.setOpenLinks(False)
        self.object = object
        self.setHtml(self.text2html(object.text or ''))
        self.anchorClicked.connect(self.on_anchor_clicked)
        self.object.subscribe(self)

    def get_state( self ):
        return state_type('text_view', self.object.get_state())

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
        asyncio.async(self.open_url(url))

    @asyncio.coroutine
    def open_url( self, url ):
        handle = yield from self.object.open_ref(url.path())
        if handle:
            self.open(handle)

    def object_changed( self ):
        self.setHtml(self.text2html(self.object.text))
        view.View.object_changed(self)

    def __del__( self ):
        log.info('~text_view %r', self)


view_registry.register('text_view', View.from_state)
