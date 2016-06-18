import os.path
import asyncio
import uuid
from PySide import QtCore, QtGui
from ..common.htypes import (
    tString,
    tBaseObject,
    IfaceRegistry,
    iface_registry,
    Column,
    list_handle_type,
    )
from ..common.endpoint import Url
from .module import Module
from .objimpl_registry import objimpl_registry
from .command import Command, ElementCommand
from .list_object import Element, Slice, ListObject
from .proxy_object import execute_get_request
from . import list_view
from .named_url_file_repository import NamedUrl, UrlFileRepository


class Bookmarks(object):

    def __init__( self, repository ):
        assert isinstance(repository, UrlFileRepository), repr(repository)
        self._repository = repository
        self._items = list(self._repository.enumerate())  # NamedUrl list
        self._id2item = dict((item.id, item) for item in self._items)

    def get_items( self ):
        return self._items

    def get_item( self, id ):
        return self._id2item[id]

    def add( self, name, url ):
        id = str(uuid.uuid4())
        item = NamedUrl(id, name, url)
        self._items.append(item)
        self._id2item[item.id] = item
        self._repository.add(item)
        return item


bookmark_list_type = tBaseObject
bookmark_list_handle_type = list_handle_type('bookmark_list', tString)


class BookmarkList(ListObject):

    @classmethod
    def from_state( cls, state, server=None ):
        return cls(iface_registry, this_module.bookmarks)
    
    def __init__( self, iface_registry, bookmarks ):
        assert isinstance(iface_registry, IfaceRegistry), repr(iface_registry)
        assert isinstance(bookmarks, Bookmarks), repr(bookmarks)
        ListObject.__init__(self)
        self._iface_registry = iface_registry
        self._bookmarks = bookmarks

    @staticmethod
    def get_state():
        return bookmark_list_type('bookmark_list')

    def get_title( self ):
        return 'Bookmarks'

    def get_commands( self ):
        return [Command('add', 'Add', 'Add url from clipboard', 'Ins')]

    @asyncio.coroutine
    def run_command( self, command_id, **kw ):
        if command_id == 'open':
            return (yield from self.run_command_open(**kw))
        if command_id == 'add':
            return (yield from self.run_command_add(**kw))
        return (yield from ListObject.run_command(self, command_id, **kw))

    @asyncio.coroutine
    def run_command_open( self, element_key ):
        item = self._bookmarks.get_item(element_key)
        return (yield from execute_get_request(item.url))

    @asyncio.coroutine
    def run_command_add( self ):
        url_str = QtGui.QApplication.clipboard().text()
        url = Url.from_str(self._iface_registry, url_str)
        name = 'Imported url'
        item = self._bookmarks.add(name, url)
        return make_bookmark_list(item.id)

    def get_columns( self ):
        return [
            Column('id'),
            Column('name', 'Bookmark name'),
            ]

    def get_key_column_id( self ):
        return 'id'

    @asyncio.coroutine
    def fetch_elements( self, sort_column_id, key, desc_count, asc_count ):
        self._notify_fetch_result(self._get_slice())

    def _get_slice( self ):
        items = self._bookmarks.get_items()
        return Slice('id', None, 'asc', list(map(self._item2element, items)), bof=True, eof=True)

    def _item2element( self, item ):
        assert isinstance(item, NamedUrl), repr(item)
        commands = [ElementCommand('open', 'Open', 'Open selected bookmark')]
        return Element(item.id, item, commands=commands)


def make_bookmark_list( key=None ):
    ## object = BookmarkList(iface_registry, this_module.bookmarks)
    object = BookmarkList.get_state()
    return bookmark_list_handle_type('list', object, sort_column_id='name', key=key)


class ThisModule(Module):

    def __init__( self ):
        Module.__init__(self)
        self.bookmarks = Bookmarks(UrlFileRepository(
            iface_registry, os.path.expanduser('~/.local/share/hyperapp/client/bookmarks')))
        objimpl_registry.register('bookmark_list', BookmarkList.from_state)

    def get_commands( self ):
        return [Command('bookmark_list', 'Bookmarks', 'Open bookmark list', 'Alt+B')]

    def get_object_commands( self, object ):
        if object.get_url() is not None:
            return [Command('bookmark', 'Bookmark', 'Add this url to bookmarks', 'Ctrl+D')]
        return []

    @asyncio.coroutine
    def run_command( self, command_id ):
        if command_id == 'bookmark_list':
            return self.run_command_bookmark_list()
        return (yield from Module.run_command(self, command_id))

    def run_command_bookmark_list( self ):
        return make_bookmark_list()

    @asyncio.coroutine
    def run_object_command( self, command_id, object ):
        if command_id == 'bookmark':
            return self.run_object_command_bookmark(object)
        return (yield from Module.run_object_command(self, command_id, object))

    def run_object_command_bookmark( self, object ):
        url = object.get_url()
        assert url is not None
        item = self.bookmarks.add(object.get_title(), url)
        return make_bookmark_list(item.id)


this_module = ThisModule()
