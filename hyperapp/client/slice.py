

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
        pass

    def pick_chunk(self, key, desc_count, asc_count):
        if key is None:
            if self.bof:
                return self
            else:
                return None



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
