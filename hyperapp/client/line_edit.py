# line edit component / widget

import logging
from PySide import QtCore, QtGui
## from util import key_match
from . import view
## from text_obj import TextObj

log = logging.getLogger(__name__)


class Handle(view.Handle):

    def __init__( self, text=None ):
        view.Handle.__init__(self)
        self.text = text

    def construct( self, parent ):
        log.info('line_edit construct parent=%r text=%r', parent, self.text)
        return View(parent, self.text)


class View(view.View, QtGui.QLineEdit):

    def __init__( self, parent, text ):
        QtGui.QLineEdit.__init__(self, text)
        view.View.__init__(self, parent)

    def handle( self ):
        return Handle(self.text())

    ## def keyPressEvent( self, evt ):
    ##     if key_match(evt, 'Return') and self._accept():
    ##         evt.accept()
    ##         return
    ##     QtGui.QLineEdit.keyPressEvent(self, evt)

    ## def _accept( self ):
    ##     text = self.text()
    ##     if not text:
    ##         return False
    ##     self._parent().object_selected(TextObj(text))
    ##     return True

    def __del__( self ):
        log.info('~line_edit')
