from operator import attrgetter
from functools import total_ordering
import logging

from .util import is_list_inst
from .diff import Diff
from .command import Command

log = logging.getLogger(__name__)


MIN_ROWS_RETURNED = 100


@total_ordering
class Element(object):

    @classmethod
    def from_data(cls, iface, rec):
        key = getattr(rec.row, iface.get_key_column_id())
        return cls(key, rec.row, [Command(id) for id in rec.commands])

    def __init__(self, key, row, commands=None, order_key=None):
        assert is_list_inst(commands or [], Command), repr(commands)
        self.key = key
        self.row = row
        self.commands = commands or []
        self.order_key = order_key  # may be None

    def __repr__(self):
        return '<Element #%r order_key=%r %r>' % (self.key, self.order_key, self.row)

    def to_data(self, iface):
        assert isinstance(iface, ListInterface), repr(iface)
        return iface.Element(self.row, [cmd.id for cmd in self.commands])

    def __eq__(self, other):
        if isinstance(other, Element):
            return self.key == other.key
        else:
            return self.key == other

    def __lt__(self, other):
        if isinstance(other, Element):
            return (self.order_key, self.key) < (other.order_key, other.key)
        else:
            return (self.order_key < other)

    def clone_with_sort_column(self, sort_column_id):
        order_key = getattr(self.row, sort_column_id)
        return Element(self.key, self.row, self.commands, order_key)


class Chunk(object):

    def __init__(self, sort_column_id, from_key, elements, bof, eof):
        assert isinstance(sort_column_id, str), repr(sort_column_id)
        assert is_list_inst(elements, Element), repr(elements)
        self.sort_column_id = sort_column_id
        self.from_key = from_key
        self.elements = elements
        self.bof = bof
        self.eof = eof

    def __eq__(self, other):
        if not isinstance(other, Chunk):
            return False
        return (self.sort_column_id == other.sort_column_id
                and self.from_key == other.from_key
                and self.elements == other.elements
                and self.bof == other.bof
                and self.eof == other.eof)

    def __repr__(self):
        return ('Chunk(sort_column_id=%r from_key=%r bof=%r eof=%r %d elements %s)'
                % (self.sort_column_id, self.from_key, self.bof, self.eof, len(self.elements),
                   '%r-%r' % (self.elements[0].key, self.elements[-1].key) if self.elements else ''))

    def to_data(self, iface):
        assert isinstance(iface, ListInterface), repr(iface)
        elements = [elt.to_data(iface) for elt in self.elements]
        return iface.Chunk(self.sort_column_id, self.from_key, elements, self.bof, self.eof)

    def clone(self, from_key=None, elements=None, bof=None):
        if from_key is None:
            from_key = self.from_key
        if elements is None:
            elements = self.elements
        if bof is None:
            bof = self.bof
        return Chunk(self.sort_column_id, from_key, elements, bof, self.eof)


class ListDiff(Diff):

    @classmethod
    def add_one(cls, element):
        return cls([], [element])

    @classmethod
    def add_many(cls, elements):
        return cls([], elements)

    @classmethod
    def replace(cls, key, element):
        return cls([key], [element])

    @classmethod
    def delete(cls, key):
        return cls([key], [])

    @classmethod
    def from_data(cls, iface, rec):
        return cls(rec.remove_keys, [Element.from_data(iface, element) for element in rec.elements])

    def __init__(self, remove_keys, elements):
        assert isinstance(remove_keys, list), repr(remove_keys)
        assert is_list_inst(elements, Element), repr(elements)
        self.remove_keys = remove_keys
        self.elements = elements

    def __repr__(self):
        return 'ListDiff(-%r+%r)' % (self.remove_keys, self.elements)

    def to_data(self, iface):
        assert isinstance(iface, ListInterface), repr(iface)
        return iface.Diff(self.remove_keys, [element.to_data(iface) for element in self.elements])


def rows2fetched_chunk(key_column_id, all_rows, fetch_request, Chunk):
    sorted_rows = sorted(all_rows, key=attrgetter(fetch_request.sort_column_id))
    if fetch_request.from_key is None:
        idx = 0
    else:
        for idx, row in enumerate(sorted_rows):
            if getattr(row, key_column_id) > fetch_request.from_key:
                break
        else:
            idx = len(sorted_rows)
    start = max(0, idx - fetch_request.desc_count)
    end = idx + fetch_request.asc_count
    if end - start < MIN_ROWS_RETURNED:
        end = start + MIN_ROWS_RETURNED
        if end < idx + 1:
            end = idx + 1
    if end > len(sorted_rows):
        end = len(sorted_rows)
    rows = sorted_rows[start:end]
    bof = start == 0
    eof = end == len(sorted_rows)
    return Chunk(fetch_request.sort_column_id, fetch_request.from_key, rows, bof, eof)
