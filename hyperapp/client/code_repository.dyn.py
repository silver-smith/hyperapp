# code repository proxy

import os
import logging
import asyncio
import uuid
from PySide import QtCore, QtGui
from ..common.htypes import (
    tString,
    tObject,
    tBaseObject,
    iface_registry,
    Column,
    list_handle_type,
    )
from ..common.interface import code_repository as code_repository_types
from ..common.interface.form import tStringFieldHandle, tFormField, tFormHandle
from ..common.url import Url
from .module import Module
from .request import Request
from .server import Server
from .proxy_object import ProxyObject
from .command import open_command
from .object import Object
from .list_object import Element, Slice, ListObject
from .named_url_file_repository import NamedUrl, NamedUrlRepository, FileNamedUrlRepository

log = logging.getLogger(__name__)


def register_object_implementations( registry, services ):
    registry.register('code_repository_form', CodeRepositoryFormObject.from_state, services.iface_registry, services.code_repository)
    registry.register('code_repository_list', CodeRepositoryList.from_state, services.code_repository)


class CodeRepository(object):

    def __init__( self, iface_registry, remoting, cache_repository, url_repository ):
        assert isinstance(url_repository, NamedUrlRepository), repr(url_repository)
        self._iface_registry = iface_registry
        self._remoting = remoting
        self._cache_repository = cache_repository
        self._url_repository = url_repository
        self._items = list(self._url_repository.enumerate())  # NamedUrl list

    def set_url_repository( self, url_repository ):
        self._url_repository = url_repository

    def get_items( self ):
        return self._items

    def add( self, name, url ):
        assert url.iface is code_repository_types.code_repository, repr(url.iface.iface_id)
        id = str(uuid.uuid4())
        item = NamedUrl(id, name, url)
        self._items.append(item)
        self._url_repository.add(item)
        return item

    # todo: try all items
    @asyncio.coroutine
    def get_modules_by_ids( self, module_ids ):
        if not self._items:
            return (None, None, None)
        proxy = CodeRepositoryProxy.from_url(self._iface_registry, self._remoting, self._cache_repository, self._items[0].url)
        return (yield from proxy.get_modules_by_ids(module_ids))

    # todo: try all items
    @asyncio.coroutine
    def get_modules_by_requirements( self, requirements ):
        if not self._items:
            log.warn('No available code repository servers are found')
            return (None, None, None)
        proxy = CodeRepositoryProxy.from_url(self._iface_registry, self._remoting, self._cache_repository, self._items[0].url)
        return (yield from proxy.get_modules_by_requirements(requirements))


class CodeRepositoryProxy(ProxyObject):

    @classmethod
    def from_url( cls, iface_registry, remoting, cache_repository, url ):
        assert isinstance(url, Url), repr(url)
        server = Server.from_public_key(remoting, url.public_key)
        return cls(iface_registry, cache_repository, server, url.path, url.iface)
        
    def __init__( self, iface_registry, cache_repository, server, path, iface, facets=None ):
        assert iface is code_repository_types.code_repository, repr(iface.iface_id)
        ProxyObject.__init__(self, iface_registry, cache_repository, server, path, iface, facets)

    @asyncio.coroutine
    def get_modules_by_ids( self, module_ids ):
        result = yield from self.execute_request('get_modules_by_ids', module_ids=module_ids)
        return (result.type_modules, result.code_modules, result.resources)

    @asyncio.coroutine
    def get_modules_by_requirements( self, requirements ):
        result = yield from self.execute_request('get_modules_by_requirements', requirements=requirements)
        return (result.type_modules, result.code_modules, result.resources)


tFormObject = tObject.register('code_repository_form', base=tBaseObject)

class CodeRepositoryFormObject(Object):

    @classmethod
    def from_state( cls, state, iface_registry, code_repository ):
        return cls(iface_registry, code_repository)

    def __init__( self, iface_registry, code_repository ):
        assert isinstance(code_repository, CodeRepository), repr(code_repository)
        Object.__init__(self)
        self.iface_registry = iface_registry
        self.code_repository = code_repository

    @staticmethod
    def get_state():
        return tFormObject('code_repository_form')

    def get_title( self ):
        return 'Add code repository'

    @open_command('_submit')
    def command_submit( self, name, url ):
        log.info('adding code repository %r...', name)
        url_ = Url.from_str(self.iface_registry, url)
        item = self.code_repository.add(name, url_)
        log.info('adding code repository %r, id=%r: done', item.name, item.id)
        return make_code_repository_list(name)


def make_code_repository_form( url_str ):
    object = CodeRepositoryFormObject.get_state()
    return tFormHandle('form', object, [
        tFormField('name', tStringFieldHandle('string', 'default repository')),
        tFormField('url', tStringFieldHandle('string', url_str)),
        ])


code_repository_list_type = tBaseObject
code_repository_list_handle_type = list_handle_type('code_repository_list', tString)


class CodeRepositoryList(ListObject):

    @classmethod
    def from_state( cls, state, code_repository ):
        return cls(code_repository)
    
    def __init__( self, code_repository ):
        assert isinstance(code_repository, CodeRepository), repr(code_repository)
        ListObject.__init__(self)
        self.code_repository = code_repository

    @staticmethod
    def get_state():
        return code_repository_list_type('code_repository_list')

    def get_title( self ):
        return 'Code repository list'

    @open_command('add')
    def command_add( self ):
        url_str = QtGui.QApplication.clipboard().text()
        return make_code_repository_form(url_str)

    def get_columns( self ):
        return [Column('name')]

    def get_key_column_id( self ):
        return 'name'

    @asyncio.coroutine
    def fetch_elements( self, sort_column_id, key, desc_count, asc_count ):
        self._notify_fetch_result(self._get_slice())

    def _get_slice( self ):
        items = self.code_repository.get_items()
        return Slice('name', None, 'asc', list(map(self._item2element, items)), bof=True, eof=True)

    def _item2element( self, item ):
        assert isinstance(item, NamedUrl), repr(item)
        return Element(item.name, item, commands=[])


def make_code_repository_list( key=None ):
    object = CodeRepositoryList.get_state()
    return code_repository_list_handle_type('list', object, ['client_module', 'code_repository_list'], sort_column_id='name', key=key)


class ThisModule(Module):

    def __init__( self, services ):
        Module.__init__(self, services)
        services.code_repository = CodeRepository(
            services.iface_registry, services.remoting, services.cache_repository,
            FileNamedUrlRepository(services.iface_registry, os.path.expanduser('~/.local/share/hyperapp/client/code_repositories')))

    @open_command('repository_list')
    def command_repository_list( self ):
        return make_code_repository_list()

    def get_object_commands( self, object ):
        if code_repository_types.code_repository in object.get_facets():
            return [self.object_command_add_to_repository_list]
        return []

    @open_command('add_to_repository_list', kind='object')
    def object_command_add_to_repository_list( self, object ):
        assert code_repository_types.code_repository in object.get_facets()
        url = object.get_url().clone(iface=code_repository_types.code_repository)
        return make_code_repository_form(url.to_str())
