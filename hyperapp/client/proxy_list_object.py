import logging
import asyncio
import weakref
import bisect
from ..common.htypes import TOptional, Field, TRecord, TList, IfaceCommand
from ..common.list_object import Element, Chunk, ListDiff
from .list_object import ListObject
from .remoting import RequestError
from .proxy_object import RemoteCommand, ProxyObject
from .slice import SliceList


log = logging.getLogger(__name__)


def register_object_implementations(registry, services):
    ProxyListObject.register(registry, services)


class ProxyListObject(ProxyObject, ListObject):

    objimpl_id = 'proxy_list'
    
    def __init__( self, packet_types, core_types, iface_registry, cache_repository,
                  resources_manager, param_editor_registry, server, path, iface, facets=None ):
        log.debug('new ProxyListObject self=%r path=%r', id(self), path)
        ProxyObject.__init__(self, packet_types, core_types, iface_registry, cache_repository,
                             resources_manager, param_editor_registry, server, path, iface, facets)
        ListObject.__init__(self)
        self._actual_key2element = {}
        self._cached_key2element = {}
        self._actual_slices = {}  # sort_column_id -> SliceList, actual, up-do-date slices
        self._slices_from_cache = {}  # sort_column_id -> SliceList, slices loaded from cache, possibly out-of-date
        self._subscribed = False
        self._subscribe_pending = False  # subscribe method is called and response is not yet received
        self._element_commands = {command.command_id: self.remote_command_from_iface_command(command, kind='element')
                                  for command in self.iface.get_commands() if self._is_element_command(command)}

    def set_contents(self, contents):
        self._log_slices('before set_contents')
        ProxyObject.set_contents(self, contents)
        chunk = self._chunk_from_data(contents.chunk)
        self._actual_slices.clear()
        self._add_fetched_chunk(chunk)
        # set_contents call means this object is returned from server and thus already subscribed
        self._subscribed = True

    @asyncio.coroutine
    def server_subscribe(self):
        pass

    def is_iface_command_exposed(self, command):
        if self._is_element_command(command): return False
        return ProxyObject.is_iface_command_exposed(self, command)

    def _is_element_command(self, command):
        command_fields = command.params_type.fields
        element_field = Field('element_key', self.iface.get_key_type())
        return (command.request_type == IfaceCommand.rt_request
                and len(command_fields) >= 1
                and command_fields[0] == element_field)

    def _is_plain_open_handle_element_request(self, command):
        t_empty_result = TRecord([])
        t_open_result = TRecord([
            Field('handle', TOptional(self._core_types.handle)),
            ])
        element_field = Field('element_key', self.iface.get_key_type())
        return (command.request_type == IfaceCommand.rt_request
                and command.params_type.fields == [element_field]
                and command.result_type in [t_empty_result, t_open_result])

    @asyncio.coroutine
    def run_remote_command(self, command_id, *args, **kw):
        command = self.iface.get_command(command_id)
        if self._is_plain_open_handle_element_request(command):
            log.debug('running remote element command %r (*%s, **%s)', command_id, args, kw)
            result = yield from self.execute_request(command_id, *args, **kw)
            if command.result_type != TRecord([]):
                return result.handle
        else:
            return (yield from ProxyObject.run_remote_command(self, command_id, *args, **kw))

    def _chunk_from_data(self, rec):
        elements = [self._element_from_data(elt, rec.sort_column_id) for elt in rec.elements]
        return Chunk(rec.sort_column_id, rec.from_key, elements, rec.bof, rec.eof)

    def _list_diff_from_data(self, rec):
        key_column_id = self.get_key_column_id()
        return ListDiff(rec.remove_keys, [self._element_from_data(elt) for elt in rec.elements])

    def _element_from_data(self, rec, sort_column_id=None):
        element = Element.from_data(self.iface, rec)
        if sort_column_id is None:
            order_key = None
        else:
            order_key = getattr(rec.row, sort_column_id)
        return self._map_element_commands(element, order_key)

    def _map_element_commands(self, element, order_key=None):
        return Element(element.key, element.row,
                       [self._element_commands[command.id] for command in element.commands],
                       order_key)

    def _map_list_diff_commands(self, diff):
        return ListDiff(diff.remove_keys, [self._map_element_commands(element) for element in diff.elements])

    def _add_fetched_chunk(self, chunk):
        log.info('  -- add_fetched_chunk self=%r chunk=%r', id(self), chunk)
        slice_list = self._actual_slices.setdefault(chunk.sort_column_id, SliceList(self._actual_key2element, chunk.sort_column_id))
        slice_list.add_fetched_chunk(chunk)
        self._log_slices('after _add_fetched_chunks')
        self._store_slices_to_cache(chunk.sort_column_id)

    def _log_slices(self, when):
        log.debug('  -- proxy list object %s %s:', id(self), when)
        for sort_column_id, slice_list in self._actual_slices.items():
            log.debug('    -- sort_column_id: %r', slice_list.sort_column_id)
            for i, slice in enumerate(slice_list.slice_list):
                log.debug('      -- slice #%d: %r', i, slice)

    def _merge_in_diff(self, diff):
        log.info('  -- merge_in_diff self=%r diff: %r', id(self), diff)
        for slice_list in self._actual_slices.values():
            slice_list.merge_in_diff(diff)
                    
    def _get_slice_list_cache_key(self, sort_column_id):
        return self.make_cache_key('chunks-%s' % sort_column_id)

    def _get_elements_cache_key(self):
        return self.make_cache_key('elements')

    def _store_slices_to_cache(self, sort_column_id):
        cache_key = self._get_slice_list_cache_key(sort_column_id)
        slice_list = self._actual_slices.get(sort_column_id)
        if not slice_list: return
        self.cache_repository.store_value(cache_key, slice_list.to_data(self.iface), SliceList.data_t(self.iface))
        self._cached_key2element.update(self._actual_key2element)
        cached_elements_data = [element.to_data(self.iface) for element in self._cached_key2element.values()]
        self.cache_repository.store_value(self._get_elements_cache_key(), cached_elements_data, TList(self.iface.Element))

    def _ensure_slices_from_cache_are_loaded(self, sort_column_id):
        if sort_column_id in self._slices_from_cache: return  # already loaded
        cached_elements_data = self.cache_repository.load_value(self._get_elements_cache_key(), TList(self.iface.Element))
        cached_elements = [self._element_from_data(data) for data in cached_elements_data or []]
        self._cached_key2element.update({
            element.key: element for element in cached_elements})
        cache_key = self._get_slice_list_cache_key(sort_column_id)
        slice_list_data = self.cache_repository.load_value(cache_key, SliceList.data_t(self.iface))
        if not slice_list_data: return
        self._slices_from_cache[sort_column_id] = SliceList.from_data(self._cached_key2element, slice_list_data)

    def process_diff(self, diff):
        assert isinstance(diff, ListDiff), repr(diff)
        log.info('-- proxy process_diff self=%r diff=%r', id(self), diff)
        mapped_diff = self._map_list_diff_commands(diff)
        self._merge_in_diff(mapped_diff)
        self._notify_diff_applied(mapped_diff)

    def get_columns(self):
        return self.iface.get_columns()

    def get_key_column_id(self):
        return self.iface.get_key_column_id()

    @asyncio.coroutine
    def fetch_elements(self, sort_column_id, from_key, desc_count, asc_count):
        log.info('-- proxy fetch_elements self=%r subscribed=%r from_key=%r desc_count=%r asc_count=%r',
                 id(self), self._subscribed, from_key, desc_count, asc_count)
        actual_slice_list = self._actual_slices.get(sort_column_id)
        chunk = None
        if actual_slice_list:
            chunk = actual_slice_list.pick_chunk(sort_column_id, from_key, desc_count, asc_count)
        if chunk:
            log.info('   > actual: %r', chunk)
            # return result even if it is stale, for faster gui response, will refresh when server response will be available
            self._notify_fetch_result(chunk)
            if self._subscribed:  # otherwise our _actual_slices may already be outdated, need to subscribe and refetch anyway
                return chunk
        else:
            self._ensure_slices_from_cache_are_loaded(sort_column_id)
            cached_slice_list = self._slices_from_cache.get(sort_column_id)
            if cached_slice_list:
                chunk = cached_slice_list.pick_chunk(sort_column_id, from_key, desc_count, asc_count)
                if chunk:
                    log.info('   > cached: %r', chunk)
                    self._notify_fetch_result(chunk)
                    # and subscribe/fetch anyway
        log.info('-- proxy fetch_elements: not found or not subscribed, requesting')
        subscribing_now = not self._subscribed and not self._subscribe_pending
        command_id = 'subscribe_and_fetch_elements' if subscribing_now else 'fetch_elements'
        if subscribing_now:
            # several views can call fetch_elements before response is received, and we do not want several subscribe_xxx calls
            self._subscribe_pending = True
        try:
            result = yield from self.execute_request(command_id, sort_column_id, from_key, desc_count, asc_count)
        except RequestError as x:
            log.warning('Error fetching elements from remote object; will use cached (%s)' % x)
            return chunk
        if subscribing_now:
            self._subscribe_pending = False
            self._subscribed = True
            ProxyObject.set_contents(self, result)
            self._notify_object_changed()
        return self._process_fetch_elements_result(result)

    def _process_fetch_elements_result(self, result):
        chunk = self._chunk_from_data(result.chunk)
        log.debug('-- proxy_list_object.fetch_elements (self=%s) result chunk: %r', id(self), chunk)
        self._add_fetched_chunk(chunk)
        self._notify_fetch_result(chunk)
        return chunk

    def __del__(self):
        log.debug('~ProxyListObject self=%r path=%r', id(self), self.path)
