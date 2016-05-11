# code repository proxy

import os.path
import glob
import uuid
from PySide import QtCore, QtGui
from ..common.htypes import (
    tString,
    Field,
    TRecord,
    tUrl,
    tObject,
    tBaseObject,
    IfaceRegistry,
    iface_registry,
    Column,
    list_handle_type,
    )
from ..common.interface.code_repository import code_repository_iface, code_repository_browser_iface
from ..common.endpoint import Url
from ..common.packet_coders import packet_coders
from .module import Module
from .request import Request
from .server import Server
from .objimpl_registry import objimpl_registry
from .proxy_object import ProxyObject
from .command import Command
from .object import Object
from .list_object import Element, Slice, ListObject
from .import form_view
from . import list_view


class Item(object):

    type = TRecord([
        Field('name', tString),
        Field('url', tUrl),
        ])

    @classmethod
    def from_data( cls, iface_registry, id, rec ):
        assert isinstance(rec, cls.type), repr(rec)
        return cls(id, rec.name, Url.from_data(iface_registry, rec.url))

    def __init__( self, id, name, url ):
        assert isinstance(id, basestring), repr(id)
        assert isinstance(name, basestring), repr(name)
        assert isinstance(url, Url), repr(url)
        self.id = id
        self.name = name
        self.url = url

    def to_data( self ):
        return self.type(self.name, self.url.to_data())


class FileUrlRepository(object):

    fext = '.url'
    encoding = 'json_pretty'

    def __init__( self, iface_registry, dir ):
        assert isinstance(iface_registry, IfaceRegistry), repr(iface_registry)
        self.iface_registry = iface_registry
        self.dir = dir

    def enumerate( self ):
        for fpath in glob.glob(os.path.join(self.dir, '*' + self.fext)):
            yield self._load_item(fpath)

    def add( self, item ):
        assert isinstance(item, Item), repr(item)
        self._save_item(item)

    def _load_item( self, fpath ):
        fname = os.path.basename(fpath)
        name, ext = os.path.splitext(fname)  # file name is Item.id
        with open(fpath) as f:
            data = f.read()
        rec = packet_coders.decode(self.encoding, data, Item.type)
        return Item.from_data(self.iface_registry, name, rec)

    def _save_item( self, item ):
        if not os.path.isdir(self.dir):
            os.makedirs(self.dir)
        data = packet_coders.encode(self.encoding, item.to_data(), Item.type)
        fpath = os.path.join(self.dir, item.id + self.fext)
        with open(fpath, 'w') as f:
            f.write(data)


class CodeRepositoryController(object):

    def __init__( self, url_repository ):
        assert isinstance(url_repository, FileUrlRepository), repr(url_repository)
        self._url_repository = url_repository
        self._items = list(self._url_repository.enumerate())  # Item list

    def get_items( self ):
        return self._items

    def add( self, name, url ):
        id = str(uuid.uuid4())
        item = Item(id, name, url)
        self._items.append(item)
        self._url_repository.add(item)
        return item


tFormObject = tObject.register('code_repository_form', base=tBaseObject)

class CodeRepositoryFormObject(Object):

    @classmethod
    def from_data( cls, data, server=None ):
        return CodeRepositoryFormObject(this_module.code_repository_controller)

    def __init__( self, controller ):
        assert isinstance(controller, CodeRepositoryController), repr(controller)
        Object.__init__(self)
        self.controller = controller

    def get_title( self ):
        return 'Create identity'

    def to_data( self ):
        return tFormObject('code_repository_form')

    def get_commands( self ):
        return [Command('submit', 'Add', 'Add new code repository', 'Return')]

    def run_command( self, command_id, initiator_view=None, **kw ):
        if command_id == 'submit':
            return self.run_command_submit(initiator_view, **kw)
        return Object.run_command(self, command_id, initiator_view, **kw)

    def run_command_submit( self, initiator_view, name, url ):
        print 'adding code repository %r...' % name
        url_ = Url.from_str(iface_registry, url)
        item = self.controller.add(name, url_)
        print 'adding code repository %r, id=%r: done' % (item.name, item.id)
        return make_code_repository_list(name)


def make_code_repository_form( url_str ):
    return form_view.Handle(CodeRepositoryFormObject(this_module.code_repository_controller), [
        form_view.Field('name', form_view.StringFieldHandle('default repository')),
        form_view.Field('url', form_view.StringFieldHandle(url_str)),
        ])


code_repository_list_type = tBaseObject
code_repository_list_handle_type = list_handle_type('code_repository_list', tString)


class CodeRepositoryList(ListObject):

    @classmethod
    def from_data( cls, objinfo, server=None ):
        return cls(this_module.code_repository_controller)
    
    def __init__( self, controller ):
        assert isinstance(controller, CodeRepositoryController), repr(controller)
        ListObject.__init__(self)
        self.controller = controller

    def get_title( self ):
        return 'Code repository list'

    def get_commands( self ):
        return [Command('add', 'Add', 'Create code repository url from clipboard', 'Ins')]

    def run_command( self, command_id, initiator_view=None, **kw ):
        if command_id == 'add':
            return self.run_command_add(initiator_view, **kw)
        return ListObject.run_command(self, command_id, initiator_view, **kw)

    def run_command_add( self, initiator_view ):
        url_str = QtGui.QApplication.clipboard().text()
        return make_code_repository_form(url_str)

    def to_data( self ):
        return code_repository_list_type('code_repository_list')

    def get_columns( self ):
        return [Column('name', 'Code Repository name')]

    def get_key_column_id( self ):
        return 'name'

    def fetch_elements( self, sort_column_id, key, desc_count, asc_count ):
        self._notify_fetch_result(self._get_slice())

    def _get_slice( self ):
        items = self.controller.get_items()
        return Slice('name', None, 'asc', map(self._item2element, items), bof=True, eof=True)

    def _item2element( self, item ):
        assert isinstance(item, Item), repr(item)
        return Element(item.name, item, commands=[])


def make_code_repository_list( key=None ):
    object = CodeRepositoryList(this_module.code_repository_controller)
    return list_view.Handle(code_repository_list_handle_type, object, sort_column_id='name', key=key)


class GetModulesRequest(Request):

    def __init__( self, iface, path, command_id, params, continuation ):
        Request.__init__(self, iface, path, command_id, params)
        self.continuation = continuation

    def process_response( self, server, response ):
        self.continuation(response.result.modules)


class CodeRepositoryProxy(ProxyObject):

    def __init__( self, server ):
        path = ['code_repository', 'code_repository']
        ProxyObject.__init__(self, server, path, code_repository_iface)

    def get_modules_and_continue( self, module_ids, continuation ):
        command_id = 'get_modules_by_ids'
        params = self.iface.make_params(command_id, module_ids=module_ids)
        request = GetModulesRequest(self.iface, self.path, command_id, params, continuation)
        self.server.execute_request(request)

    def get_required_modules_and_continue( self, requirements, continuation ):
        command_id = 'get_modules_by_requirements'
        params = self.iface.make_params(command_id, requirements=requirements)
        request = GetModulesRequest(self.iface, self.path, command_id, params, continuation)
        self.server.execute_request(request)


class ThisModule(Module):

    def __init__( self ):
        Module.__init__(self)
        self.code_repository_controller = CodeRepositoryController(
            FileUrlRepository(iface_registry, os.path.expanduser('~/.local/share/hyperapp/client/code_repositories')))
        objimpl_registry.register('code_repository_form', CodeRepositoryFormObject.from_data)
        objimpl_registry.register('code_repository_list', CodeRepositoryList.from_data)

    def get_object_commands( self, object ):
        if code_repository_iface in object.get_facets():
            return [Command('add_to_repository_list', 'Add Repository', 'Add this repository to my repositories list', 'Ctrl+A')]
        return []

    def run_object_command( self, command_id, object ):
        if command_id == 'add_to_repository_list':
            return self.run_object_command_add_to_repository_list(object)
        return Module.run_object_command(self, command_id)

    def run_object_command_add_to_repository_list( self, object ):
        assert code_repository_iface in object.get_facets()
        url = object.get_url().clone(iface=code_repository_iface)
        return make_code_repository_form(url.to_str())


this_module = ThisModule()
