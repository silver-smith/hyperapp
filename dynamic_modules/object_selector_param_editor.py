import os.path
import logging
import asyncio
from PySide import QtCore, QtGui
from ..common.interface import article as article_types
from ..common.interface import core as core_types
from .util import uni2str
from . import view
from .command import command, ViewCommand

log = logging.getLogger(__name__)


def register_param_editors( registry, services ):
    registry.register(View.impl_id, View.resolve_param_editor, services.iface_registry)

def register_views( registry, services ):
    registry.register(View.view_id, View.from_state, services.objimpl_registry, services.view_registry)



def get_default_url( server, iface_registry ):
    iface = iface_registry.resolve('fs_dir')
    return server.make_url(iface, ['file', os.path.expanduser('~')])

    
class View(view.View, QtGui.QWidget):

    impl_id = 'object_selector'
    view_id = 'object_selector'

    @classmethod
    def resolve_param_editor( cls, state, proxy_object, command_id, iface_registry ):
        ref_list = proxy_object.get_state()
        target_url = get_default_url(proxy_object.server, iface_registry)
        target_handle = core_types.redirect_handle(view_id='redirect', redirect_to=target_url.to_data())
        return article_types.object_selector_handle(cls.view_id, ref_list, target_handle)

    @classmethod
    @asyncio.coroutine
    def from_state( cls, locale, state, parent, objimpl_registry, view_registry ):
        ref_list = objimpl_registry.resolve(state.ref_list)
        target_view = yield from view_registry.resolve(locale, state.target)
        return cls(parent, ref_list, target_view)

    def __init__( self, parent, ref_list, target_view ):
        QtGui.QWidget.__init__(self)
        view.View.__init__(self, parent)
        self.ref_list = ref_list
        self.target_view = target_view
        target_view.set_parent(self)
        self.groupBox = QtGui.QGroupBox('Select object for %s' % self.ref_list.get_title())
        gbl = QtGui.QVBoxLayout()
        gbl.addWidget(self.target_view.get_widget())
        self.groupBox.setLayout(gbl)
        l = QtGui.QVBoxLayout()
        l.addWidget(self.groupBox)
        self.setLayout(l)

    def get_state( self ):
        return article_types.object_selector_handle(self.view_id, self.ref_list.get_state(), self.target_view.get_state())

    def get_current_child( self ):
        return self.target_view

    def get_object( self ):
        return self.ref_list

    def get_commands( self, kinds ):
        return (self.target_view.get_commands(kinds)
                + view.View.get_commands(self, kinds)
                + [self.object_command_choose])  # do not wrap in ViewCommand - we will open it ourselves

    @command('choose', kind='object')
    @asyncio.coroutine
    def object_command_choose( self ):
        url = self.target_view.get_url()
        if not url: return  # not a proxy - can not choose it
        result = (yield from self.ref_list.run_command('add', target_url=url.to_data()))
        view.View.open(self, result.handle)  # do not wrap in our handle

    def open( self, handle ):
        handle = article_types.object_selector_handle(self.view_id, self.ref_list.get_state(), handle)
        view.View.open(self, handle)

    def __del__( self ):
        log.info('~object_selector.View')
