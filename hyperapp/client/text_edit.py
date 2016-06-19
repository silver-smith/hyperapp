import logging
import asyncio
from PySide import QtCore, QtGui
from ..common.htypes import tObjHandle
from .objimpl_registry import objimpl_registry
from .view_registry import view_registry
from . import view
from .text_object import TextObject

log = logging.getLogger(__name__)


state_type = tObjHandle


class View(view.View, QtGui.QTextEdit):

    @classmethod
    @asyncio.coroutine
    def from_state( cls, state, parent ):
        object = objimpl_registry.produce_obj(state.object)
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

    def get_object_commands( self ):
        return view.View.get_object_commands(self, TextObject.mode_edit)

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


view_registry.register('text_edit', View.from_state)
