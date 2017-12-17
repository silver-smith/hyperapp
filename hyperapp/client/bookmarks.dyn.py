import os.path
import uuid
from PySide import QtCore, QtGui
from ..common.htypes import (
    tString,
    IfaceRegistry,
    Column,
    list_handle_type,
    )
from ..common.interface import packet as packet_types
from ..common.interface import core as core_types
from ..common.url import Url
from .module import Module
from .named_url_file_repository import FileNamedUrlRepository
from .command import command
from .remoting import Remoting
from .list_object import Element, Chunk, ListObject
from .proxy_object import execute_get_request
from .named_url_file_repository import NamedUrl, NamedUrlRepository


def register_object_implementations(registry, services):
    registry.register(BookmarkList.objimpl_id, BookmarkList.from_state,
                      services.iface_registry, services.remoting, services.bookmarks)


class Bookmarks(object):

    def __init__(self, repository):
        assert isinstance(repository, NamedUrlRepository), repr(repository)
        self._repository = repository
        self._items = list(self._repository.enumerate())  # NamedUrl list
        self._id2item = dict((item.id, item) for item in self._items)

    def get_items(self):
        return self._items

    def get_item(self, id):
        return self._id2item[id]

    def add(self, name, url):
        id = str(uuid.uuid4())
        item = NamedUrl(id, name, url)
        self._items.append(item)
        self._id2item[item.id] = item
        self._repository.add(item)
        return item


bookmark_list_type = core_types.object_base
bookmark_list_handle_type = list_handle_type(core_types, tString)


class BookmarkList(ListObject):

    objimpl_id = 'bookmark_list'

    @classmethod
    def from_state(cls, state, iface_registry, remoting, bookmarks):
        return cls(iface_registry, remoting, bookmarks)
    
    def __init__(self, iface_registry, remoting, bookmarks):
        assert isinstance(iface_registry, IfaceRegistry), repr(iface_registry)
        assert isinstance(remoting, Remoting), repr(remoting)
        assert isinstance(bookmarks, Bookmarks), repr(bookmarks)
        ListObject.__init__(self)
        self._iface_registry = iface_registry
        self._remoting = remoting
        self._bookmarks = bookmarks

    @classmethod
    def get_state(cls):
        return bookmark_list_type(cls.objimpl_id)

    def get_title(self):
        return 'Bookmarks'

    @command('open', kind='element')
    async def command_open_bookmark(self, element_key):
        item = self._bookmarks.get_item(element_key)
        return (await execute_get_request(packet_types, self._remoting, item.url))

    @command('add')
    async def command_add(self):
        url_str = QtGui.QApplication.clipboard().text()
        url = Url.from_str(self._iface_registry, url_str)
        name = 'Imported url'
        item = self._bookmarks.add(name, url)
        return make_bookmark_list(item.id)

    def get_columns(self):
        return [
            Column('id'),
            Column('name'),
            ]

    def get_key_column_id(self):
        return 'id'

    async def fetch_elements(self, sort_column_id, key, desc_count, asc_count):
        self._notify_fetch_result(self._get_chunk())

    def _get_chunk(self):
        items = self._bookmarks.get_items()
        return Chunk('id', None, list(map(self._item2element, items)), bof=True, eof=True)

    def _item2element(self, item):
        assert isinstance(item, NamedUrl), repr(item)
        commands = [self.command_open_bookmark]
        return Element(item.id, item, commands=commands)


def make_bookmark_list(key=None):
    object = BookmarkList.get_state()
    return bookmark_list_handle_type('list', object, ['client_module', 'bookmarks', 'BookmarkList'], sort_column_id='id', key=key)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self.bookmarks = Bookmarks(FileNamedUrlRepository(
            services.iface_registry, os.path.expanduser('~/.local/share/hyperapp/client/bookmarks')))
        services.bookmarks = self.bookmarks

    def get_object_command_list(self, object, kinds=None):
        if object.get_url() is not None:
            return [self.object_command_bookmark]
        return []

    @command('bookmark_list')
    def command_bookmark_list(self):
        return make_bookmark_list()

    @command('bookmark', kind='object')
    def object_command_bookmark(self, object):
        url = object.get_url()
        assert url is not None
        item = self.bookmarks.add(object.get_title(), url)
        return make_bookmark_list(item.id)
