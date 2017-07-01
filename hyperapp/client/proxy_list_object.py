import logging
import asyncio
import weakref
import bisect
from ..common.htypes import TOptional, Field, TRecord, TList, IfaceCommand
from .list_object import ListDiff, Element, Slice, ListObject
from .remoting import RequestError
from .proxy_object import RemoteCommand, ProxyObject

log = logging.getLogger(__name__)


def register_object_implementations(registry, services):
    ProxyListObject.register(registry, services)


class SliceAlgorithm(object):

    def merge_in_slice(self, slices, new_slice):
        if new_slice.elements:
            log.info('      elements[0].key=%r elements[-1].key=%r', new_slice.elements[0].key, new_slice.elements[-1].key)
        for slice in slices:
            if slice.sort_column_id != new_slice.sort_column_id: continue
            if new_slice.from_key == slice.elements[-1].key:
                assert not new_slice.bof  # this is continuation for existing slice, bof is not possible
                slice.elements.extend(new_slice.elements)
                slice.eof = new_slice.eof
                log.info('     > merged len(elements)=%r elements[0].key=%r elements[-1].key=%r', len(slice.elements), slice.elements[0].key, slice.elements[-1].key)
                break
            if not new_slice.elements: continue
            if new_slice.elements[0].key > slice.elements[-1].key: continue
            if new_slice.elements[-1].key < slice.elements[0].key: continue
            # now we know we have an intersection
            assert False, 'todo: implement slice intersections'
        else:
            slices.append(new_slice)
            log.info('     > added')

    def pick_slice(self, slices, sort_column_id, from_key, desc_count, asc_count):
        for slice in slices:
            if slice.sort_column_id != sort_column_id: continue
            if from_key == None:
                if slice.bof:
                    log.info('     > bof found, len(elements)=%r', len(slice.elements))
                    return slice
                else:
                    continue
            log.info('       - checking len(elements)=%r elements[0].order_key=%r elements[-1].order_key=%r', len(slice.elements), slice.elements[0].order_key, slice.elements[-1].order_key)
            # here we assume sort_column_id == key_column_id, other sort order is todo:
            if slice.elements[0].order_key <= from_key <= slice.elements[-1].order_key:
                idx = bisect.bisect_left(slice.elements, from_key)  # must be from_order_key
                log.info('     - bisecting idx=%r', idx)
                while slice.elements[idx].order_key <= from_key:  # from_order_key
                    idx += 1
                    if slice.elements[idx-1].key == from_key: break  # from_order_key
                log.info('     - exact key idx=%r', idx)
                if idx < len(slice.elements):
                    log.info('     > middle found idx=%r len(elements)=%r len(elements[idx:])=%r', idx, len(slice.elements), len(slice.elements[idx:]))
                    idx = max(idx - desc_count, 0)
                    return slice.clone_with_elements(slice.elements[idx:])
        log.info('     > none found')
        return None  # none found


class ProxyListObject(ProxyObject, ListObject):

    objimpl_id = 'proxy_list'
    
    def __init__( self, request_types, core_types, iface_registry, cache_repository,
                  resources_manager, param_editor_registry, server, path, iface, facets=None ):
        ProxyObject.__init__(self, request_types, core_types, iface_registry, cache_repository,
                             resources_manager, param_editor_registry, server, path, iface, facets)
        ListObject.__init__(self)
        self._slice_algorithm = SliceAlgorithm()
        self._slices = []  # all slices are stored in ascending order, guaranteed actual/up-do-date
        self._slices_from_cache = {}  # key_column_id -> Slice list, slices loaded from cache, possibly out-of-date
        self._subscribed = False
        self._subscribe_pending = False  # subscribe method is called and response is not yet received
        self._element_commands = {command.command_id: self.remote_command_from_iface_command(command, kind='element')
                                  for command in self.iface.get_commands() if self._is_element_command(command)}

    def set_contents(self, contents):
        self._log_slices('before set_contents')
        ProxyObject.set_contents(self, contents)
        slice = self._slice_from_data(contents.slice)
        self._slices = [slice]
        # set_contents call means this object is returned from server and thus already subscribed
        self._subscribed = True

    @asyncio.coroutine
    def server_subscribe(self):
        pass

    def is_iface_command_exposed(self, command):
        if self._is_element_command(command): return False
        return ProxyObject.is_iface_command_exposed(self, command)

    def _is_element_command(self, command):
        command_fields = command.params_type.get_fields()
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
                and command.params_type.get_fields() == [element_field]
                and command.result_type in [t_empty_result, t_open_result])

    @asyncio.coroutine
    def run_remote_command(self, command_id, *args, **kw):
        if self._is_plain_open_handle_element_request(self.iface.get_command(command_id)):
            log.debug('running remote element command %r (*%s, **%s)', command_id, args, kw)
            result = yield from self.execute_request(command_id, *args, **kw)
            return result.handle
        else:
            return (yield from ProxyObject.run_remote_command(self, command_id, *args, **kw))

    def _slice_from_data(self, rec):
        key_column_id = self.get_key_column_id()
        elements = [self._element_from_data(key_column_id, rec.sort_column_id, elt) for elt in rec.elements]
        return Slice(rec.sort_column_id, rec.from_key, elements, rec.bof, rec.eof)

    def _list_diff_from_data(self, key_column_id, rec):
        return ListDiff(rec.start_key, rec.end_key, [self._element_from_data(key_column_id, None, elt) for elt in rec.elements])

    def _element_from_data(self, key_column_id, sort_column_id, rec):
        key = getattr(rec.row, key_column_id)
        if sort_column_id is None:
            order_key = None
        else:
            order_key = getattr(rec.row, sort_column_id)
        commands = [self._element_command_from_data(command_id) for command_id in  rec.commands]
        return Element(key, rec.row, commands, order_key)

    def _element_command_from_data(self, command_id):
        return self._element_commands[command_id]

    def _merge_in_slice(self, new_slice):
        log.info('  -- merge_in_slice self=%r from_key=%r len(elements)=%r bof=%r', id(self), new_slice.from_key, len(new_slice.elements), new_slice.bof)
        self._slice_algorithm.merge_in_slice(self._slices, new_slice)
        self._log_slices('after _merge_in_slices')
        self._store_slices_to_cache(new_slice.sort_column_id)

    def _log_slices(self, when):
        log.debug('  -- proxy list object %s has total %d slices %s:', id(self), len(self._slices), when)
        for i, slice in enumerate(self._slices):
            log.debug('    -- slice #%d has from_key=%r bof=%r eof=%r %d elements: %s',
                      i, slice.from_key, slice.bof, slice.eof, len(slice.elements), ', '.join(str(element.key) for element in slice.elements))

    def _update_slices(self, diff):
        log.info('  -- update_slices self=%r diff: start_key=%r end_key=%r len(elements)=%r', id(self), diff.start_key, diff.end_key, len(diff.elements))
        for slice in self._slices:
            for idx in reversed(range(len(slice.elements))):
                element = slice.elements[idx]
                if diff.start_key <= element.key and element.key <= diff.end_key:
                    del slice.elements[idx]
                    log.info('-- slice with sort %r: element is deleted at %d', slice.sort_column_id, idx)
            for new_elt in diff.elements:
                new_elt = new_elt.clone_with_sort_column(slice.sort_column_id)
                for idx in range(len(slice.elements)):
                    assert len(diff.elements) <= 1, len(diff.elements)  # inserting more than one elements at once is not yet supported
                    order_key = slice.elements[idx].order_key
                    if idx == 0:
                        if new_elt.order_key <= order_key and slice.bof:
                            slice.elements.insert(0, new_elt)
                            log.info('-- slice with sort %r: element is inserted to begin of slice', slice.sort_column_id)
                            break
                    else:
                        prev_order_key = slice.elements[idx - 1].order_key
                        if prev_order_key <= new_elt.order_key and new_elt.order_key <= order_key:
                            slice.elements.insert(idx, new_elt)
                            log.info('-- slice with sort %r: element is inserted at idx %d', slice.sort_column_id, idx)
                            break
                if slice.elements:
                    order_key = slice.elements[-1].order_key
                    if new_elt.order_key > order_key and slice.eof:
                        slice.elements.append(new_elt)
                        log.info('-- slice with sort %r: element is appended to the end of slice', slice.sort_column_id)
                    
    def _pick_slice(self, slices, sort_column_id, from_key, desc_count, asc_count):
        log.info('  -- pick_slice self=%r sort_column_id=%r from_key=%r', id(self), sort_column_id, from_key)
        return SliceAlgorithm().pick_slice(slices, sort_column_id, from_key, desc_count, asc_count)

    def _get_slice_cache_key(self, sort_column_id):
        return self.make_cache_key('slices-%s' % sort_column_id)

    def _get_slices_cache_type(self):
        return TList(self.iface.tSlice())

    def _store_slices_to_cache(self, sort_column_id):
        key = self._get_slice_cache_key(sort_column_id)
        slices = [slice.to_data(self.iface) for slice in self._slices if slice.sort_column_id == sort_column_id]
        self.cache_repository.store_value(key, slices, self._get_slices_cache_type())

    def _ensure_slices_from_cache_loaded(self, sort_column_id):
        if sort_column_id in self._slices_from_cache: return  # already loaded
        key = self._get_slice_cache_key(sort_column_id)
        slice_recs = self.cache_repository.load_value(key, self._get_slices_cache_type())
        self._slices_from_cache[sort_column_id] = list(map(self._slice_from_data, slice_recs or []))

    def put_back_slice(self, slice):
        log.info('-- proxy put_back_slice self=%r len(elements)=%r', id(self), len(slice.elements))
        assert isinstance(slice, Slice), repr(slice)
        self._merge_in_slice(slice)

    def process_update(self, diff):
        log.info('-- proxy process_update self=%r diff=%r start_key=%r end_key=%r elements=%r', id(self), diff, diff.start_key, diff.end_key, diff.elements)
        key_column_id = self.get_key_column_id()
        diff = self._list_diff_from_data(key_column_id, diff)
        self._update_slices(diff)
        self._notify_diff_applied(diff)

    def get_columns(self):
        return self.iface.get_columns()

    def get_key_column_id(self):
        return self.iface.get_key_column_id()

    @asyncio.coroutine
    def fetch_elements(self, sort_column_id, from_key, desc_count, asc_count):
        log.info('-- proxy fetch_elements self=%r subscribed=%r from_key=%r desc_count=%r asc_count=%r',
                 id(self), self._subscribed, from_key, desc_count, asc_count)
        slice = self._pick_slice(self._slices, sort_column_id, from_key, desc_count, asc_count)
        if slice:
            log.info('   > from object: %r', slice)
            # return result even if it is stale, for faster gui response, will refresh when server response will be available
            self._notify_fetch_result(slice)
            if self._subscribed:  # otherwise our _slices may already be outdated, need to subscribe and refetch anyway
                return slice
        else:
            self._ensure_slices_from_cache_loaded(sort_column_id)
            cached_slices = self._slices_from_cache.get(sort_column_id, [])
            slice = self._pick_slice(cached_slices, sort_column_id, from_key, desc_count, asc_count)
            if slice:
                log.info('   > from cache, len(elements)=%r', len(slice.elements))
                self._notify_fetch_result(slice)
                # and subscribe/fetch anyway
        log.info('   > not found or not subscribed, requesting')
        subscribing_now = not self._subscribed and not self._subscribe_pending
        command_id = 'subscribe_and_fetch_elements' if subscribing_now else 'fetch_elements'
        if subscribing_now:
            # several views can call fetch_elements before response is received, and we do not want several subscribe_xxx calls
            self._subscribe_pending = True
        try:
            result = yield from self.execute_request(command_id, sort_column_id, from_key, desc_count, asc_count)
            log.debug('proxy_list_object fetch_elements result self=%r, slice: %r', id(self), slice)
        except RequestError as x:
            log.warning('Error fetching elements from remote object; will use cached (%s)' % x)
            return slice
        if subscribing_now:
            self._subscribe_pending = False
            self._subscribed = True
            ProxyObject.set_contents(self, result)
            self._notify_object_changed()
        return self._process_fetch_elements_result(result)

    def _process_fetch_elements_result(self, result):
        slice = self._slice_from_data(result.slice)
        self._merge_in_slice(slice)
        self._notify_fetch_result(slice)
        return slice

    def __del__(self):
        log.info('~ProxyListObject self=%r path=%r', id(self), self.path)
