from .list_object import ListDiff, Element, Slice, ListObject
from .proxy_object import ProxyObject
from .proxy_registry import proxy_registry


class ProxyListObject(ProxyObject, ListObject):

    def __init__( self, server, path, iface ):
        ProxyObject.__init__(self, server, path, iface)
        ListObject.__init__(self)
        self._default_sort_column_id = None
        self._slices = []  # all slices are stored in ascending order

    @staticmethod
    def get_proxy_id():
        return 'list'

    def set_contents( self, contents ):
        ProxyObject.set_contents(self, contents)
        slice = self._decode_slice(contents.slice)
        self._default_sort_column_id = slice.sort_column_id
        self._merge_in_slice(slice)

    def get_default_sort_column_id( self ):
        assert self._default_sort_column_id  # there were no set_contents calls
        return self._default_sort_column_id

    def _decode_slice( self, rec ):
        key_column_id = self.get_key_column_id()
        elements = [Element.decode(key_column_id, rec.sort_column_id, elt_rec) for elt_rec in rec.elements]
        return Slice(rec.sort_column_id, rec.from_key, rec.direction, elements, rec.bof, rec.eof)

    def _merge_in_slice( self, new_slice ):
        print '  -- merge_in_slice', id(self), repr(new_slice.from_key), len(new_slice.elements), new_slice.bof
        if new_slice.elements: print '      ', repr(new_slice.elements[0].key), repr(new_slice.elements[-1].key)
        for slice in self._slices:
            if slice.sort_column_id != new_slice.sort_column_id: continue
            assert new_slice.direction == 'asc'  # todo: desc direction
            if new_slice.from_key == slice.elements[-1].key:
                assert not new_slice.bof  # this is continuation for existing slice, bof is not possible
                slice.elements.extend(new_slice.elements)
                slice.eof = new_slice.eof
                print '     > merged', len(slice.elements), repr(slice.elements[0].key), repr(slice.elements[-1].key)
                break
        else:
            self._slices.append(new_slice)
            print '     > added'

    def _update_slices( self, diff ):
        for slice in self._slices:
            for idx in reversed(range(len(slice.elements))):
                element = slice.elements[idx]
                if diff.start_key <= element.key and element.key <= diff.end_key:
                    del slice.elements[idx]
                    print '-- slice with sort %r: element is deleted at %d' % (slice.sort_column_id, idx)
            for new_elt in diff.elements:
                new_elt = new_elt.clone_with_sort_column(slice.sort_column_id)
                for idx in range(len(slice.elements)):
                    assert len(diff.elements) <= 1, len(diff.elements)  # inserting more than one elements at once is not yet supported
                    order_key = slice.elements[idx].order_key
                    if idx == 0:
                        if new_elt.order_key <= order_key and slice.bof:
                            slice.elements.insert(0, new_elt)
                            print '-- slice with sort %r: element is inserted to begin of slice' % slice.sort_column_id
                            break
                    else:
                        prev_order_key = slice.elements[idx - 1].order_key
                        if prev_order_key <= new_elt.order_key and new_elt.order_key <= order_key:
                            slice.elements.insert(idx, new_elt)
                            print '-- slice with sort %r: element is inserted at idx %d' % (slice.sort_column_id, idx)
                            break
                if slice.elements:
                    order_key = slice.elements[-1].order_key
                    if new_elt.order_key > order_key and slice.eof:
                        slice.elements.append(new_elt)
                        print '-- slice with sort %r: element is appended to the end of slice' % slice.sort_column_id
                    

    def _pick_slice( self, sort_column_id, from_key, direction ):
        print '  -- pick_slice', id(self), repr(sort_column_id), repr(from_key), direction
        assert direction == 'asc'  # todo: desc direction
        for slice in self._slices:
            if slice.sort_column_id != sort_column_id: continue
            if from_key == None and slice.bof:
                print '     > bof found', len(slice.elements)
                return slice
            print '       - checking', len(slice.elements), repr(slice.elements[0].order_key), repr(slice.elements[-1].order_key)
            # here we assume sort_column_id == key_column_id:
            if slice.elements[0].order_key <= from_key and from_key <= slice.elements[-1].order_key:
                idx = bisect.bisect_left(slice.elements, from_key)  # must be from_order_key
                print '     - bisecting', idx
                while slice.elements[idx].order_key <= from_key:  # from_order_key
                    idx += 1
                    if slice.elements[idx-1].key == from_key: break  # from_order_key
                print '     - exact key', idx
                if idx < len(slice.elements):
                    print '     > middle found', idx, len(slice.elements), len(slice.elements[idx:])
                    return slice.clone_with_elements(slice.elements[idx:])
        print '     > none found'
        return None  # none found
            
    def subscribe_and_fetch_elements( self, observer, sort_column_id, from_key, direction, count ):
        this_is_first_observer = self.subscribe_local(observer)
        print '-- proxy subscribe_and_fetch_elements', this_is_first_observer, self, observer
        if not this_is_first_observer:
            return False
        slice = self._pick_slice(sort_column_id, from_key, direction)
        if slice:
            print '   > cached', len(slice.elements)
            self._notify_fetch_result(slice)
        else:
            print '   > no cached, requesting'
            self.execute_request('subscribe_and_fetch_elements', None, sort_column_id, from_key, direction, count)
        return True

    def process_update( self, diff ):
        print 'process_update', self, diff, diff.start_key, diff.end_key, diff.elements
        key_column_id = self.get_key_column_id()
        diff = ListDiff.decode(key_column_id, diff)
        self._update_slices(diff)
        self._notify_diff_applied(diff)

    def get_columns( self ):
        return self.iface.columns

    def get_key_column_id( self ):
        return self.iface.key_column

    def fetch_elements( self, sort_column_id, from_key, direction, count ):
        print '-- proxy fetch_elements', self, repr(from_key), count
        slice = self._pick_slice(sort_column_id, from_key, direction)
        if slice:
            print '   > cached', len(slice.elements)
            self._notify_fetch_result(slice)
        else:
            print '   > no cached, requesting'
            self.execute_request('fetch_elements', None, sort_column_id, from_key, direction, count)

    def process_response_result( self, command_id, result ):
        if command_id == 'subscribe_and_fetch_elements':
            self.process_subscribe_and_fetch_elements_result(result)
        elif command_id == 'fetch_elements':
            self.process_fetch_elements_result(result)
        else:
            ProxyObject.process_response_result(self, command_id, result)

    def process_subscribe_and_fetch_elements_result( self, result ):
        print '-- proxy process_subscribe_and_fetch_elements_result', self, len(result.slice.elements)
        ProxyObject.set_contents(self, result)
        slice = self._decode_slice(result.slice)
        self._merge_in_slice(slice)
        self._notify_object_changed()
        self._notify_fetch_result(slice)

    def process_fetch_elements_result( self, result ):
        print '-- proxy process_fetch_elements_result', self, len(result.slice.elements)
        slice = self._decode_slice(result.slice)
        self._merge_in_slice(slice)
        self._notify_fetch_result(slice)

    def __del__( self ):
        print '~ProxyListObject', self, self.path


proxy_registry.register_class(ProxyListObject)
