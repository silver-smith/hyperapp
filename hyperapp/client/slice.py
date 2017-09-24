import bisect
from ..common.list_object import Chunk


class Slice(object):

    def __init__(self, key2element, sort_column_id, bof, eof, keys):
        self.key2element = key2element
        self.sort_column_id = sort_column_id
        self.bof = bof
        self.eof = eof
        self.keys = keys

    def __repr__(self):
        return '<%s bof=%s eof=%s %s>' % (self.sort_column_id, self.bof, self.eof, self.keys)

    def __eq__(self, other):
        return (self.sort_column_id == other.sort_column_id and
                self.bof == other.bof and
                self.eof == other.eof and
                self.keys == other.keys)

    def add_fetched_chunk(self, chunk):
        self.key2element.update({element.key: element for element in chunk.elements})
        if chunk.bof:
            assert chunk.from_key is None, repr(chunk.from_key)
            start_idx = 0
            self.bof = True
        else:
            assert chunk.from_key is not None and chunk.from_key in self.keys, repr(chunk.from_key)  # valid from_key is expected for non-bof chunks
            start_idx = self.keys.index(chunk.from_key) + 1
        # elements after this chunk are removed from self.keys
        self.keys = self.keys[:start_idx] + [element.key for element in chunk.elements]
        self.eof = chunk.eof

    def merge_in_diff(self, diff):
        self.key2element.update({element.key: element for element in diff.elements})
        self.keys = [key for key in self.keys if key not in diff.remove_keys]
        for element in diff.elements:
            idx = bisect.bisect(self._ordered_elements(self.keys), element)
            if idx == 0 and not self.bof:
                continue  # before first element - ignore if not bof
            if idx == len(self.keys) and not self.eof:
                continue  # after last element - ignore if not eof
            self.keys.insert(idx, element.key)

    def pick_chunk(self, key, desc_count, asc_count):
        if key is None:
            if self.bof:
                idx = 0
            else:
                return None
        else:
            try:
                idx = self.keys.index(key)
            except ValueError:
                return None  # Unknown key
        start = max(0, idx - desc_count)
        end = min(len(self.keys), idx + asc_count)
        if start == 0:
            if self.bof:
                from_key = None
            else:
                from_key = self.keys[start]
                start += 1
        else:
            from_key = self.keys[start - 1]
        keys = self.keys[start:end]
        bof = self.bof and start == 0
        eof = self.eof and end == len(self.keys)
        return Chunk(self.sort_column_id, from_key, self._ordered_elements(keys), bof=bof, eof=eof)

    def _ordered_elements(self, keys ):
        return [self.key2element[key].clone_with_sort_column(self.sort_column_id) for key in keys]


class SliceList(object):

    def __init__(self, sort_column_id):
        self.sort_column_id = sort_column_id
        self.slice_list = []

    def pick_slice(self, sort_column_id, key, desc_count, asc_count):
        if sort_column_id != self.sort_column_id:
            return None
        for slice in self.slice_list:
            chunk = slice.pick_chunk(key, desc_count, asc_count)
            if chunk:
                return chunk
        return None  # none found
