import logging
import asyncio
from PySide import QtCore, QtGui
from ..common.interface.article import tObjSelectorHandle
from .util import uni2str
from .objimpl_registry import objimpl_registry
from .proxy_object import ProxyObject
from .view_registry import view_registry
from . import view
from .command import ObjectCommand

log = logging.getLogger(__name__)


def register_views( registry ):
    registry.register(View.view_id, View.from_state)


class View(view.View, QtGui.QWidget):

    view_id = 'object_selector'

    @classmethod
    @asyncio.coroutine
    def from_state( cls, state, parent ):
        ref = objimpl_registry.produce_obj(state.ref)
        target_view = yield from view_registry.resolve(state.target)
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

    def get_object_commands( self ):
        commands = self.target_view.get_object_commands()
        choose_cmd = ObjectCommand(self, 'choose', 'Choose', 'Choose current object', 'Ctrl+Return')
        return [choose_cmd] + commands

    @asyncio.coroutine
    def run_object_command( self, command_id ):
        if command_id == 'choose':
            yield from self.run_object_command_choose(command_id)
        else:
            return (yield from self.target_view.run_object_command(command_id))

    @asyncio.coroutine
    def run_object_command_choose( self, command_id ):
        target_obj = self.target_view.get_object()
        url = target_obj.get_url()
        if not url: return  # not a proxy - can not choose it
        handle = (yield from self.ref.run_command(command_id, target_url=url.to_data()))
        if handle:
            view.View.open(self, handle)  # do not wrap in our handle

    def open( self, handle ):
        handle = tObjSelectorHandle(self.view_id, self.ref.get_state(), handle)
        view.View.open(self, handle)

    def __del__( self ):
        log.info('~object_selector.View')
