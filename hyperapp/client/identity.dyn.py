import os
import os.path
import glob
import logging
from ..common.htypes import (
    tString,
    list_handle_type,
    Column,
    )
from ..common.interface import core as core_types
from ..common.interface import form as form_types
from ..common.identity import Identity
from .command import command
from .module import Module
from .object import Object
from .list_object import Element, Chunk, ListObject
#from .form import formHandle

log = logging.getLogger(__name__)


def register_object_implementations(registry, services):
    registry.register(IdentityFormObject.impl_id, IdentityFormObject.from_state, services.identity_controller)
    registry.register(IdentityList.impl_id, IdentityList.from_state, services.identity_controller)


class IdentityItem(object):

    def __init__(self, name, identity):
        assert isinstance(name, str), repr(name)
        assert isinstance(identity, Identity), repr(identity)
        self.name = name
        self.identity = identity


class IdentityRepository(object):

    def add(self, identity_item):
        raise NotImplementedError(self.__class__)

    def enumerate(self):
        raise NotImplementedError(self.__class__)


class FileIdentityRepository(IdentityRepository):

    fext = '.identity'

    def __init__(self, dir):
        self.dir = dir

    def add(self, identity_item):
        assert isinstance(identity_item, IdentityItem), repr(identity_item)
        if not os.path.isdir(self.dir):
            os.makedirs(self.dir)
        fpath = os.path.join(self.dir, identity_item.name + self.fext)
        identity_item.identity.save_to_file(fpath)

    def enumerate(self):
        for fpath in glob.glob(os.path.join(self.dir, '*' + self.fext)):
            fname = os.path.basename(fpath)
            name, ext = os.path.splitext(fname)
            identity = Identity.load_from_file(fpath)
            yield IdentityItem(name, identity)


class IdentityController(object):

    def __init__(self, repository):
        ## assert isinstance(repository, IdentityRepository), repr(repository)
        self._repository = repository
        self._items = list(self._repository.enumerate())  # IdentityItem list

    def get_items(self):
        return self._items

    def generate(self, name):
        identity = Identity.generate()
        item = IdentityItem(name, identity)
        self._items.append(item)
        self._repository.add(item)


tIdentityFormObject = core_types.object.register('identity_form', base=core_types.object_base)


class IdentityFormObject(Object):

    impl_id = 'identity_form'

    @classmethod
    def from_state(cls, state, identity_controller):
        return IdentityFormObject(identity_controller)

    @classmethod
    def get_state(cls):
        return tIdentityFormObject(cls.impl_id)

    def __init__(self, identity_controller):
        Object.__init__(self)
        self.identity_controller = identity_controller

    def get_title(self):
        return 'Create identity'

    @command('submit')
    def command_submit(self, name):
        log.info('creating identity %r...', name)
        self.identity_controller.generate(name)
        log.info('creating identity %r: done', name)
        return make_identity_list(name)


def make_identity_form():
    return formHandle(IdentityFormObject.get_state(), [
        form_types.form_field('name', form_types.string_field_handle('string', 'anonymous')),
        ])


identity_list_type = core_types.object_base
identity_list_handle_type = list_handle_type(core_types, tString)


class IdentityList(ListObject):

    impl_id = 'identity_list'

    @classmethod
    def from_state(cls, state, identity_controller):
        return cls(identity_controller)
    
    def __init__(self, identity_controller):
        assert isinstance(identity_controller, IdentityController), repr(identity_controller)
        ListObject.__init__(self)
        self.identity_controller = identity_controller

    @classmethod
    def get_state(cls):
        return identity_list_type(cls.impl_id)

    def get_title(self):
        return 'Identity list'

    @command('create')
    def command_new(self):
        return make_identity_form()

    def get_columns(self):
        return [
            Column('name'),
            ]

    def get_key_column_id(self):
        return 'name'

    async def fetch_elements_impl(self, sort_column_id, key, desc_count, asc_count):
        items = self.identity_controller.get_items()
        return Chunk('name', None, list(map(self._item2element, items)), bof=True, eof=True)

    def _item2element(self, item):
        assert isinstance(item, IdentityItem), repr(item)
        return Element(item.name, item, commands=[])


def make_identity_list(key=None):
    object = IdentityList.get_state()
    return identity_list_handle_type('list', object, ['client_module', 'identity', 'IdentityList'], sort_column_id='name', key=key)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        repository = (getattr(services, 'identity_repository', None)  # overriden by test
                      or FileIdentityRepository(os.path.expanduser('~/.local/share/hyperapp/client/identities')))
        services.identity_controller = IdentityController(repository)

    @command('identity_list')
    def command_identity_list(self):
        return make_identity_list()

    @command('create_identity')
    def run_command_create_idenity(self):
        return make_identity_form()
