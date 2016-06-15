import logging
import asyncio
from PySide import QtCore, QtGui
from ..common.interface.article import tObjSelectorHandle, tObjSelectorUnwrapHandle
from .util import uni2str
from .objimpl_registry import objimpl_registry
from .proxy_object import ProxyObject
from .view_registry import view_registry
from . import view
from .command import ObjectCommand

log = logging.getLogger(__name__)


class ObjSelectorUnwrap(view.Handle):

    @classmethod
    def from_data( cls, contents, server=None ):
        base_handle = view_registry.resolve(contents.base_handle, server)
        return cls(base_handle)

    def __init__( self, base_handle ):
        self.base_handle = base_handle

    def to_data( self ):
        return tObjSelectorUnwrapHandle('object_selector_unwrap', self.base_handle.to_data())

    def get_object( self ):
        return self.base_handle.get_object()

    def get_module_ids( self ):
        return [this_module_id]

    def construct( self, parent ):
        return self.base_handle.construct(parent)


class Handle(view.Handle):

    @classmethod
    def from_data( cls, contents, server=None ):
        ref = objimpl_registry.produce_obj(contents.ref, server)
        target_handle = view_registry.resolve(contents.target, server)
        return cls(ref, target_handle)

    def __init__( self, ref, target ):
        assert isinstance(ref, ProxyObject), repr(ref)
        assert isinstance(target, view.Handle), repr(target)
        view.Handle.__init__(self)
        self.ref = ref
        self.target = target

    def to_data( self ):
        return tObjSelectorHandle('object_selector', ref=self.ref.to_data(), target=self.target.to_data())

    def get_title( self ):
        return '%s: %s' % (self.ref.get_title(), self.target.get_title())

    def get_object( self ):
        return self.ref

    def get_module_ids( self ):
        return [this_module_id]

    def construct( self, parent ):
        log.info('object_selector construct %r, %r, %r', parent, self.ref.get_title(), self.target.get_object().get_title())
        return View(parent, self.ref, self.target)

    def __repr__( self ):
        return 'object_selector.Handle(%s)' % uni2str(self.ref.get_title())


class View(view.View, QtGui.QWidget):

    def __init__( self, parent, ref, target ):
        QtGui.QWidget.__init__(self)
        view.View.__init__(self, parent)
        self.ref = ref
        self.target_view = target.construct(self)
        self.groupBox = QtGui.QGroupBox('Select object for %s' % self.ref.get_title())
        gbl = QtGui.QVBoxLayout()
        gbl.addWidget(self.target_view.get_widget())
        self.groupBox.setLayout(gbl)
        l = QtGui.QVBoxLayout()
        l.addWidget(self.groupBox)
        self.setLayout(l)

    def handle( self ):
        return Handle(self.ref, self.target_view.handle())

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
        if handle:  # command is handled by client-side
            self.open(handle)

    def open( self, handle ):
        if not isinstance(handle, ObjSelectorUnwrap):
            handle = Handle(self.ref, handle)
        view.View.open(self, handle)

    def __del__( self ):
        log.info('~object_selector.View')


view_registry.register('object_selector', Handle.from_data)
view_registry.register('object_selector_unwrap', ObjSelectorUnwrap.from_data)
