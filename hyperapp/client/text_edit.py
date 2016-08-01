import logging
import asyncio
from PySide import QtCore, QtGui
from ..common.htypes import tObjHandle
from . import view
from .text_object import TextObject

log = logging.getLogger(__name__)


state_type = tObjHandle


def register_views( registry, services ):
    registry.register('text_edit', View.from_state, services.objimpl_registry)


class View(view.View, QtGui.QTextEdit):

    @classmethod
    @asyncio.coroutine
    def from_state( cls, state, parent, objimpl_registry ):
        object = objimpl_registry.resolve(state.object)
        return cls(object, parent)

    def __init__( self, object, parent ):
        QtGui.QTextEdit.__init__(self)
        view.View.__init__(self, parent)
        self.object = object
        self.notify_on_text_changed = True
        self.setPlainText(object.text)
        self.textChanged.connect(self._on_text_changed)
        self.object.subscribe(self)

    def get_state( self ):
        return state_type('text_edit', self.object.get_state())

    def get_title( self ):
        return self.object.get_title()

    def get_object( self ):
        return self.object

    def get_object_commands( self, object ):
        return object.get_commands(TextObject.mode_edit)

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
        log.info('~text_edit %r', self)
