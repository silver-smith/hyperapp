import os
import os.path
import glob
from ..common.htypes import (
    tString,
    tObject,
    tBaseObject,
    list_handle_type,
    Column,
    )
from ..common.identity import Identity
from .objimpl_registry import objimpl_registry
from .command import Command
from .object import Object
from .list_object import Element, Slice, ListObject
from .import form_view
from . import list_view


class IdentityItem(object):

    def __init__( self, name, identity ):
        assert isinstance(name, basestring), repr(name)
        assert isinstance(identity, Identity), repr(identity)
        self.name = name
        self.identity = identity


class IdentityRepository(object):

    def add( self, identity_item ):
        raise NotImplementedError(self.__class__)

    def enumerate( self ):
        raise NotImplementedError(self.__class__)


class FileIdentityRepository(IdentityRepository):

    fext = '.identity'

    def __init__( self, dir ):
        self.dir = dir

    def add( self, identity_item ):
        assert isinstance(identity_item, IdentityItem), repr(identity_item)
        if not os.path.isdir(self.dir):
            os.makedirs(self.dir)
        fpath = os.path.join(self.dir, identity_item.name + self.fext)
        identity_item.identity.save_to_file(fpath)

    def enumerate( self ):
        for fpath in glob.glob(os.path.join(self.dir, '*' + self.fext)):
            fname = os.path.basename(fpath)
            name, ext = os.path.splitext(fname)
            identity = Identity.load_from_file(fpath)
            yield IdentityItem(name, identity)


class IdentityController(object):

    def __init__( self, repository ):
        assert isinstance(repository, IdentityRepository), repr(repository)
        self._repository = repository
        self._items = list(self._repository.enumerate())  # IdentityItem list

    def get_items( self ):
        return self._items

    def generate( self, name ):
        identity = Identity.generate()
        item = IdentityItem(name, identity)
        self._items.append(item)
        self._repository.add(item)


tIdentityFormObject = tObject.register('identity_form', base=tBaseObject)


class IdentityFormObject(Object):

    @classmethod
    def from_data( cls, data, server=None ):
        return IdentityFormObject()

    def get_title( self ):
        return 'Create identity'

    def to_data( self ):
        return tIdentityFormObject('identity_form')

    def get_commands( self ):
        return [Command('submit', 'Create', 'Create new identity, generate private+public key pair', 'Return')]

    def run_command( self, command_id, initiator_view=None, **kw ):
        if command_id == 'submit':
            return self.run_command_submit(initiator_view, **kw)
        return Object.run_command(self, command_id, initiator_view, **kw)

    def run_command_submit( self, initiator_view, name ):
        print 'creating identity %r...' % name
        identity_controller.generate(name)
        print 'creating identity %r: done' % name
        return make_identity_list(name)


def make_identity_form():
    return form_view.Handle(IdentityFormObject(), [
        form_view.Field('name', form_view.StringFieldHandle('anonymous')),
        ])


identity_list_type = tBaseObject
identity_list_handle_type = list_handle_type('identity_list', tString)


class IdentityList(ListObject):

    @classmethod
    def from_data( cls, objinfo, server=None ):
        return cls(identity_controller)
    
    def __init__( self, controller ):
        assert isinstance(controller, IdentityController), repr(controller)
        ListObject.__init__(self)
        self.controller = controller

    def get_title( self ):
        return 'Identity list'

    def get_commands( self ):
        return [Command('new', 'Create', 'Create new identity, generate private+public key pair', 'Ins')]

    def run_command( self, command_id, initiator_view=None, **kw ):
        if command_id == 'new':
            return self.run_command_new(initiator_view, **kw)
        return ListObject.run_command(self, command_id, initiator_view, **kw)

    def run_command_new( self, initiator_view ):
        return make_identity_form()

    def to_data( self ):
        return identity_list_type('identity_list')

    def get_columns( self ):
        return [
            Column('name', 'Identity name'),
            ]

    def get_key_column_id( self ):
        return 'name'

    def fetch_elements( self, sort_column_id, key, desc_count, asc_count ):
        self._notify_fetch_result(self._get_slice())

    def _get_slice( self ):
        items = self.controller.get_items()
        return Slice('name', None, 'asc', map(self._item2element, items), bof=True, eof=True)

    def _item2element( self, item ):
        assert isinstance(item, IdentityItem), repr(item)
        return Element(item.name, item, commands=[])


def make_identity_list( key=None ):
    object = IdentityList(identity_controller)
    return list_view.Handle(identity_list_handle_type, object, sort_column_id='name', key=key)


identity_controller = IdentityController(FileIdentityRepository(os.path.expanduser('~/.local/share/hyperapp/client/identities')))
objimpl_registry.register('identity_form', IdentityFormObject.from_data)
objimpl_registry.register('identity_list', IdentityList.from_data)
