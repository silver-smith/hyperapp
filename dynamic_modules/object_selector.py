import logging
import asyncio
from PySide import QtCore, QtGui
from ..common.interface.article import tObjSelectorHandle
from .util import uni2str
from .proxy_object import ProxyObject
from . import view
from .command import command, ViewCommand

log = logging.getLogger(__name__)


def register_views( registry, services ):
    registry.register(View.view_id, View.from_state, services.objimpl_registry, services.view_registry)


class View(view.View, QtGui.QWidget):

    view_id = 'object_selector'

    @classmethod
    @asyncio.coroutine
    def from_state( cls, locale, state, parent, objimpl_registry, view_registry ):
        ref = objimpl_registry.resolve(state.ref)
        target_view = yield from view_registry.resolve(locale, state.target)
        return cls(parent, ref, target_view)

    def __init__( self, parent, ref, target_view ):
        QtGui.QWidget.__init__(self)
        view.View.__init__(self, parent)
        self.ref = ref
        self.target_view = target_view
        target_view.set_parent(self)
        self.groupBox = QtGui.QGroupBox('Select object for %s' % self.ref.get_title())
        gbl = QtGui.QVBoxLayout()
        gbl.addWidget(self.target_view.get_widget())
        self.groupBox.setLayout(gbl)
        l = QtGui.QVBoxLayout()
        l.addWidget(self.groupBox)
        self.setLayout(l)

    def get_state( self ):
        return tObjSelectorHandle(self.view_id, self.ref.get_state(), self.target_view.get_state())

    def get_current_child( self ):
        return self.target_view

    def get_object( self ):
        return self.ref

    def get_commands( self, kinds ):
        return (self.target_view.get_commands(kinds)
                + view.View.get_commands(self, kinds)
                + [self.object_command_choose])  # do not wrap in ViewCommand - we will open it ourselves

    @command('choose', kind='object')
    @asyncio.coroutine
    def object_command_choose( self ):
        url = self.target_view.get_url()
        if not url: return  # not a proxy - can not choose it
        handle = (yield from self.ref.run_command('choose', target_url=url.to_data()))
        if handle:
            view.View.open(self, handle)  # do not wrap in our handle

    def open( self, handle ):
        handle = tObjSelectorHandle(self.view_id, self.ref.get_state(), handle)
        view.View.open(self, handle)

    def __del__( self ):
        log.info('~object_selector.View')
