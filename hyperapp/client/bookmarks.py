import asyncio
import uuid
from PySide import QtCore, QtGui
from ..common.htypes import (
    tString,
    tBaseObject,
    IfaceRegistry,
    Column,
    list_handle_type,
    )
from ..common.url import Url
from .module import Module
from .command import Command, ElementCommand
from .remoting import Remoting
from .list_object import Element, Slice, ListObject
from .proxy_object import execute_get_request
from .named_url_file_repository import NamedUrl, UrlFileRepository


def register_object_implementations( registry, services ):
    registry.register(BookmarkList.objimpl_id, BookmarkList.from_state,
                      services.iface_registry, services.remoting, services.bookmarks)


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

    objimpl_id = 'bookmark_list'

    @classmethod
    def from_state( cls, state, iface_registry, remoting, bookmarks ):
        return cls(iface_registry, remoting, bookmarks)
    
    def __init__( self, iface_registry, remoting, bookmarks ):
        assert isinstance(iface_registry, IfaceRegistry), repr(iface_registry)
        assert isinstance(remoting, Remoting), repr(remoting)
        assert isinstance(bookmarks, Bookmarks), repr(bookmarks)
        ListObject.__init__(self)
        self._iface_registry = iface_registry
        self._remoting = remoting
        self._bookmarks = bookmarks

    @classmethod
    def get_state( cls ):
        return bookmark_list_type(cls.objimpl_id)

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
        return (yield from execute_get_request(self._remoting, item.url))

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
    object = BookmarkList.get_state()
    return bookmark_list_handle_type('list', object, sort_column_id='name', key=key)


class ThisModule(Module):

    def __init__( self, services ):
        Module.__init__(self, services)
        self.bookmarks = services.bookmarks

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
