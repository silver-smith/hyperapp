import logging
from operator import attrgetter
from ..common.util import is_list_inst, encode_path
from ..common.htypes import (
    tString,
    tInt,
    Field,
    Interface,
    list_handle_type,
    categorized_list_handle_type,
    )
from ..common.visual_rep import pprint
from .util import WeakValueMultiDict
from .command import Commander

log = logging.getLogger(__name__)


MIN_ROWS_RETURNED = 100


class Subscription(object):

    def __init__(self):
        self.path2channel = WeakValueMultiDict()  # path -> Channel

    def add(self, path, peer_channel):
        log.info('-- subscribing %r %r', path, peer_channel.get_id())
        self.path2channel.add(encode_path(path), peer_channel)

    def remove(self, path, peer_channel):
        log.info('-- unsubscribing %r %r', path, peer_channel.get_id())
        self.path2channel.remove(encode_path(path), peer_channel)

    def distribute_update(self, iface, path, diff):
        update = iface.Update(path, diff)
        log.info('-- distributing update:')
        pprint(iface.tUpdate, update)
        for peer_channel in self.path2channel.get(encode_path(path)):
            log.info('-- sending update to %r', peer_channel.get_id())
            peer_channel.send_update(update)


subscription = Subscription()


class Object(Commander):

    facets = None

    def __init__(self, core_types=None):
        Commander.__init__(self, commands_kind='object')
        self._core_types = core_types

    def get_path(self):
        raise NotImplementedError(self.__class__)

    def get_facets(self):
        if self.facets is None:
            return [self.iface]
        else:
            return self.facets

    def get(self, request):
        path = self.get_path()
        assert is_list_inst(path, str), '%s.get_path must return list of strings, but returned: %r' % (self.__class__.__name__, path)
        return self.iface.Object(
            objimpl_id=self.objimpl_id,
            public_key_der=request.me.get_public_key().to_der(),
            iface=self.iface.iface_id,
            facets=[facet.iface_id for facet in self.get_facets()],
            path=path,
            contents=self.get_contents(request),
            )

    def get_contents(self, request, **kw):
        return self.iface.Contents(
            commands=[cmd.to_data() for cmd in self.get_commands()],
            **kw)

    def get_handle(self, request):
        raise NotImplementedError(self.__class__)

    def process_request(self, request):
        command_id = request.command_id
        if command_id == 'get':
            return self.process_request_get(request)
        if command_id == 'subscribe':
            return self.process_request_subscribe(request)
        elif command_id == 'unsubscribe':
            self.unsubscribe(request)
        else:
            command = self.get_command(command_id)
            assert command, repr(command_id)  # Unknown command
            return command.run(request)

    def process_request_get(self, request):
        return request.make_response_handle(self.get_handle(request))

    def process_request_subscribe(self, request):
        self.subscribe(request)
        return request.make_response(self.get_contents(request))

    def subscribe(self, request):
        subscription.add(self.get_path(), request.peer.channel)

    def unsubscribe(self, request):
        subscription.remove(self.get_path(), request.peer.channel)


class ListObject(Object):

    default_sort_column_id = 'key'
    iface = None  # define in subclass
    resource_id = None  # define in subclass
    categories = None  # define in subclass

    @classmethod
    def Row(cls, *args, **kw):
        return cls.iface.Row(*args, **kw)

    @classmethod
    def Element(cls, row, commands=None):
        for cmd in commands or []:
            assert cmd.kind == 'element', ('%s: command %r must has "element" kind, but has kind %r'
                                           % (cls.__name__, cmd.id, cmd.kind))
        return cls.iface.Element(row, [cmd.id for cmd in commands or []])

    @classmethod
    def Diff(cls, *args, **kw):
        return cls.iface.Diff(*args, **kw)

    @classmethod
    def Diff_replace(cls, key, element):
        return cls.Diff(key, key, [element])

    @classmethod
    def Diff_insert_one(cls, key, element):
        return cls.Diff_insert_many(key, [element])

    @classmethod
    def Diff_add_one(cls, element):
        return cls.Diff_insert_one(None, element)

    @classmethod
    def Diff_insert_many(cls, key, elements):
        return cls.Diff(key, key, elements)

    @classmethod
    def Diff_add_many(cls, elements):
        return cls.Diff.insert_many(None, elements)

    @classmethod
    def Diff_delete(cls, key):
        return cls.Diff(key, key, [])

    def __init__(self, core_types):
        Object.__init__(self, core_types)

    def get_contents(self, request, **kw):
        slice = self.fetch_elements(request, self.default_sort_column_id, None, 0, MIN_ROWS_RETURNED)
        assert isinstance(slice, self.iface.tSlice()), \
          'Invalid result returned from fetch_elements, use: return self.Slice(...); returned: %r, expected: %r' \
            % (slice, self.iface.tSlice())
        return Object.get_contents(self, request, slice=slice, **kw)

    def get_handle(self, request):
        return self.ListHandle(self.get(request))

    def process_request(self, request):
        if request.command_id == 'fetch_elements':
            return self.process_request_fetch_elements(request)
        if request.command_id == 'subscribe_and_fetch_elements':
            self.subscribe(request)
            return self.process_request_fetch_elements(request)
        elif request.command_id == 'run_element_command':
            return self.run_element_command(request, request.command_id, request.params.element_key)
        else:
            return Object.process_request(self, request)

    def process_request_fetch_elements(self, request):
        params = request.params
        slice = self.fetch_elements(request, params.sort_column_id, params.from_key, params.desc_count, params.asc_count)
        assert isinstance(slice, self.iface.tSlice()), \
          'Invalid result is returned from fetch_elements: %r; use: return self.Slice(...)' % slice
        return request.make_response(Object.get_contents(self, request, slice=slice))

    # must return Slice, construct using self.Slice(...)
    def fetch_elements(self, request, sort_column_id, key, desc_count, asc_count):
        raise NotImplementedError(self.__class__)

    def run_element_command(self, request, command_id, element_key):
        assert False, repr(command_id)  # Unexpected command_id

    def Slice(self, sort_column_id, from_key, elements, bof, eof):
        assert isinstance(sort_column_id, str), repr(sort_column_id)
        column = self._pick_column(sort_column_id)
        assert column, 'Unknown column: %r; known are: %r'\
           % (sort_column_id, [column.id for column in self.iface.get_columns()])
        return self.iface.Slice(sort_column_id, from_key, elements, bof, eof)
            
    def _pick_column(self, column_id):
        for column in self.iface.get_columns():
            if column.id == column_id:
                return column
        return None

    def ListHandle(self, object, sort_column_id=None, key=None):
        assert self.iface, '%s.iface is not defined' % self.__class__.__name__
        handle_t = list_handle_type(self._core_types, self.iface.get_key_type())
        if sort_column_id is None:
            sort_column_id = self.default_sort_column_id
        resource_id = ['interface', self.iface.iface_id]
        return handle_t('list', object, resource_id, sort_column_id, key)

    def CategorizedListHandle(self, object, sort_column_id=None, key=None):
        assert self.categories, '%s.categories is not defined' % self.__class__.__name__
        assert self.iface, '%s.iface is not defined' % self.__class__.__name__
        handle_t = categorized_list_handle_type(self._core_types, self.iface.get_key_type())
        if sort_column_id is None:
            sort_column_id = self.default_sort_column_id
        resource_id = ['interface', self.iface.iface_id]
        return handle_t('categorized_list', object, self.categories, resource_id, sort_column_id, key)


class SmallListObject(ListObject):

    def fetch_elements(self, request, sort_column_id, from_key, desc_count, asc_count):
        assert desc_count == 0, repr(desc_count)  # Not yet supported
        elt2sort_key = attrgetter('row.%s' % self.iface.get_key_column_id())
        sorted_elements = sorted(self.fetch_all_elements(request), key=elt2sort_key)
        if from_key is None:
            idx = 0
        else:
            for idx, element in enumerate(sorted_elements):
                if elt2sort_key(element) > from_key:
                    break
            else:
                idx = len(sorted_elements)
        if asc_count < MIN_ROWS_RETURNED:
            asc_count = MIN_ROWS_RETURNED
        elements = sorted_elements[idx : idx+asc_count]
        bof = idx == 0
        eof = idx + asc_count >= len(sorted_elements)
        return self.Slice(sort_column_id, from_key, elements, bof, eof)

    # must return self.iface.Element list
    def fetch_all_elements(self, request):
        raise NotImplementedError(self.__class__)
    
