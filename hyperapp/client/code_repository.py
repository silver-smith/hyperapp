# code repository proxy

import os.path
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
from ..common.interface.code_repository import code_repository_iface, code_repository_browser_iface
from ..common.interface.form import tStringFieldHandle, tFormField, tFormHandle
from ..common.endpoint import Url
from .module import Module
from .request import Request
from .server import Server
from .objimpl_registry import objimpl_registry
from .proxy_object import ProxyObject
from .command import Command
from .object import Object
from .list_object import Element, Slice, ListObject
from .named_url_file_repository import NamedUrl, UrlFileRepository

log = logging.getLogger(__name__)


class CodeRepository(object):

    def __init__( self, url_repository ):
        assert isinstance(url_repository, UrlFileRepository), repr(url_repository)
        self._url_repository = url_repository
        self._items = list(self._url_repository.enumerate())  # NamedUrl list

    def get_items( self ):
        return self._items

    def add( self, name, url ):
        assert url.iface is code_repository_iface, repr(url.iface.iface_id)
        id = str(uuid.uuid4())
        item = NamedUrl(id, name, url)
        self._items.append(item)
        self._url_repository.add(item)
        return item

    # todo: try all items
    @asyncio.coroutine
    def get_modules_by_ids( self, module_ids ):
        if not self._items: return
        proxy = CodeRepositoryProxy.from_url(self._items[0].url)
        return (yield from proxy.get_modules_by_ids(module_ids))

    # todo: try all items
    @asyncio.coroutine
    def get_modules_by_requirements( self, requirements ):
        if not self._items:
            log.warn('No available code repository servers are found')
            return
        proxy = CodeRepositoryProxy.from_url(self._items[0].url)
        return (yield from proxy.get_modules_by_requirements(requirements))


class CodeRepositoryProxy(ProxyObject):

    @classmethod
    def from_url( cls, url ):
        assert isinstance(url, Url), repr(url)
        server = Server.from_endpoint(url.endpoint)
        return cls(server, url.path, url.iface)
        
    def __init__( self, server, path, iface ):
        assert iface is code_repository_iface, repr(iface.iface_id)
        ProxyObject.__init__(self, server, path, iface)

    @asyncio.coroutine
    def get_modules_by_ids( self, module_ids ):
        result = yield from self.execute_request('get_modules_by_ids', module_ids=module_ids)
        return result.modules

    @asyncio.coroutine
    def get_modules_by_requirements( self, requirements ):
        result = yield from self.execute_request('get_modules_by_requirements', requirements=requirements)
        return result.modules


tFormObject = tObject.register('code_repository_form', base=tBaseObject)

class CodeRepositoryFormObject(Object):

    @classmethod
    def from_state( cls, state ):
        return CodeRepositoryFormObject(this_module.code_repository)

    def __init__( self, controller ):
        assert isinstance(controller, CodeRepository), repr(controller)
        Object.__init__(self)
        self.controller = controller

    @staticmethod
    def get_state():
        return tFormObject('code_repository_form')

    def get_title( self ):
        return 'Add code repository'

    def get_commands( self ):
        return [Command('submit', 'Add', 'Add new code repository', 'Return')]

    @asyncio.coroutine
    def run_command( self, command_id, **kw ):
        if command_id == 'submit':
            return self.run_command_submit(**kw)
        return (yield from Object.run_command(self, command_id, **kw))

    def run_command_submit( self, name, url ):
        log.info('adding code repository %r...', name)
        url_ = Url.from_str(iface_registry, url)
        item = self.controller.add(name, url_)
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
    def from_state( cls, state ):
        return cls(this_module.code_repository)
    
    def __init__( self, controller ):
        assert isinstance(controller, CodeRepository), repr(controller)
        ListObject.__init__(self)
        self.controller = controller

    @staticmethod
    def get_state():
        return code_repository_list_type('code_repository_list')

    def get_title( self ):
        return 'Code repository list'

    def get_commands( self ):
        return [Command('add', 'Add', 'Create code repository url from clipboard', 'Ins')]

    @asyncio.coroutine
    def run_command( self, command_id, **kw ):
        if command_id == 'add':
            return self.run_command_add(**kw)
        return (yield from ListObject.run_command(self, command_id, **kw))

    def run_command_add( self ):
        url_str = QtGui.QApplication.clipboard().text()
        return make_code_repository_form(url_str)

    def get_columns( self ):
        return [Column('name', 'Code Repository name')]

    def get_key_column_id( self ):
        return 'name'

    @asyncio.coroutine
    def fetch_elements( self, sort_column_id, key, desc_count, asc_count ):
        self._notify_fetch_result(self._get_slice())

    def _get_slice( self ):
        items = self.controller.get_items()
        return Slice('name', None, 'asc', list(map(self._item2element, items)), bof=True, eof=True)

    def _item2element( self, item ):
        assert isinstance(item, NamedUrl), repr(item)
        return Element(item.name, item, commands=[])


def make_code_repository_list( key=None ):
    object = CodeRepositoryList.get_state()
    return code_repository_list_handle_type('list', object, sort_column_id='name', key=key)


class ThisModule(Module):

    def __init__( self ):
        Module.__init__(self)
        self.code_repository = CodeRepository(
            UrlFileRepository(iface_registry, os.path.expanduser('~/.local/share/hyperapp/client/code_repositories')))
        objimpl_registry.register('code_repository_form', CodeRepositoryFormObject.from_state)
        objimpl_registry.register('code_repository_list', CodeRepositoryList.from_state)

    def get_commands( self ):
        return [Command('repository_list', 'Code repositories', 'Open code repository list', 'Alt+R')]

    @asyncio.coroutine
    def run_command( self, command_id ):
        if command_id == 'repository_list':
            return self.run_command_repository_list()
        return (yield from Module.run_command(self, command_id))

    def run_command_repository_list( self ):
        return make_code_repository_list()

    def get_object_commands( self, object ):
        if code_repository_iface in object.get_facets():
            return [Command('add_to_repository_list', 'Add Repository', 'Add this repository to my repositories list', 'Ctrl+A')]
        return []

    @asyncio.coroutine
    def run_object_command( self, command_id, object ):
        if command_id == 'add_to_repository_list':
            return self.run_object_command_add_to_repository_list(object)
        return (yield from Module.run_object_command(self, command_id))

    def run_object_command_add_to_repository_list( self, object ):
        assert code_repository_iface in object.get_facets()
        url = object.get_url().clone(iface=code_repository_iface)
        return make_code_repository_form(url.to_str())


def get_code_repository():
    return this_module.code_repository


this_module = ThisModule()
