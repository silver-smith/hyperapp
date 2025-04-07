import abc
import itertools
import logging
import weakref
from functools import cached_property

from hyperapp.boot.htypes import tInt, TList, TOptional, TRecord

from .code.tree_diff import TreeDiff
from .code.tree_visual_diff import (
    VisualTreeDiffAppend,
    VisualTreeDiffInsert,
    VisualTreeDiffReplace,
    VisualTreeDiffRemove,
    )

log = logging.getLogger(__name__)


class IndexTreeAdapterMixin:

    @cached_property
    def model_state_t(self):
        item_t = self._item_t
        return TRecord('ui_tree', f'model_state_{item_t.module_name}_{item_t.name}', {
            'current_path': TList(tInt),
            'current_item': TOptional(item_t),
            })

    def make_model_state(self, current_path, current_item):
        return self.model_state_t(
            current_path=current_path,
            current_item=current_item,
            )

    def _parent_model_kw(self, parent_id):
        return {
            'parent': self._id_to_item[parent_id],
            }

    def _apply_diff(self, diff):
        if isinstance(diff, TreeDiff.Append):
            parent_path = diff.path
        else:
            parent_path = diff.path[:-1]
        parent_id = 0
        for idx in parent_path:
            parent_id = self._get_id_list(parent_id)[idx]
        if isinstance(diff, TreeDiff.Append):
            self._append_item(parent_id, diff.item)
            return VisualTreeDiffAppend(parent_id)
        id_list = self._get_id_list(parent_id)
        idx = diff.path[-1]
        if isinstance(diff, TreeDiff.Remove):
            self._remove_item(parent_id, id_list, idx)
            return VisualTreeDiffRemove(parent_id, idx)
        item_id = next(self._id_counter)
        self._id_to_parent_id[item_id] = parent_id
        self._id_to_item[item_id] = diff.item
        if isinstance(diff, TreeDiff.Insert):
            id_list.insert(idx, item_id)
            return VisualTreeDiffInsert(parent_id, idx)
        if isinstance(diff, TreeDiff.Replace):
            id_list[idx] = item_id
            return VisualTreeDiffReplace(parent_id, idx)


class KeyTreeAdapterMixin:

    def __init__(self, key_field, key_field_t):
        self._key_field = key_field
        self._key_field_t = key_field_t
        self._parent_id_key_to_idx = {}

    @cached_property
    def model_state_t(self):
        item_t = self._item_t
        return TRecord('ui_tree', f'model_state_{item_t.module_name}_{item_t.name}', {
            'current_path': TList(self._key_field_t),
            'current_item': TOptional(item_t),
            })

    def make_model_state(self, current_path, current_item):
        key_path = []
        item_id = 0
        for idx in current_path:
            id_list = self._get_id_list(item_id)
            item_id = id_list[idx]
            item = self._id_to_item[item_id]
            key = getattr(item, self._key_field)
            key_path.append(key)
        return self.model_state_t(
            current_path=tuple(key_path),
            current_item=current_item,
            )

    def _parent_model_kw(self, parent_id):
        return {
            'current_path': self._make_key_path(parent_id),
            }

    def _make_key_path(self, item_id):
        if item_id == 0:
            return []
        path = []
        item = self._id_to_item[item_id]
        key = getattr(item, self._key_field)
        parent_id = self._id_to_parent_id[item_id]
        return [*self._make_key_path(parent_id), key]

    def _get_key_idx(self, parent_id, key):
        try:
            return self._parent_id_key_to_idx[parent_id, key]
        except KeyError:
            pass
        self._update_key_indexes(parent_id)
        return self._parent_id_key_to_idx[parent_id, key]

    def _update_key_indexes(self, parent_id):
        id_list = self._get_id_list(parent_id)
        for idx, item_id in enumerate(id_list):
            item = self._id_to_item[item_id]
            item_key = getattr(item, self._key_field)
            self._parent_id_key_to_idx[parent_id, item_key] = idx

    def _apply_diff(self, diff):
        if isinstance(diff, TreeDiff.Append):
            parent_key_path = diff.path
        else:
            parent_key_path = diff.path[:-1]
        parent_id = 0
        for key in parent_key_path:
            id_list = self._get_id_list(parent_id)
            idx = self._get_key_idx(parent_id, key)
            parent_id = id_list[idx]
        if isinstance(diff, TreeDiff.Append):
            self._append_item(parent_id, diff.item)
            self._update_key_indexes(parent_id)
            return VisualTreeDiffAppend(parent_id)
        id_list = self._get_id_list(parent_id)
        key = diff.path[-1]
        idx = self._get_key_idx(parent_id, key)
        if isinstance(diff, TreeDiff.Remove):
            self._remove_item(parent_id, id_list, idx)
            del self._parent_id_key_to_idx[parent_id, key]
            self._update_key_indexes(parent_id)
            return VisualTreeDiffRemove(parent_id, idx)
        item_id = next(self._id_counter)
        self._id_to_parent_id[item_id] = parent_id
        self._id_to_item[item_id] = diff.item
        if isinstance(diff, TreeDiff.Insert):
            id_list.insert(idx, item_id)
            self._update_key_indexes(parent_id)
            return VisualTreeDiffInsert(parent_id, idx)
        if isinstance(diff, TreeDiff.Replace):
            id_list[idx] = item_id
            self._update_key_indexes(parent_id)
            return VisualTreeDiffReplace(parent_id, idx)


class TreeAdapterBase(metaclass=abc.ABCMeta):

    def __init__(self, model, item_t):
        self._model = model
        self._item_t = item_t
        self._id_to_item = {0: None}
        self._id_to_children_id_list = {}
        self._id_to_parent_id = {}
        self._id_counter = itertools.count(start=1)
        self._subscribers = weakref.WeakSet()

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    @property
    def model(self):
        return self._model

    def row_id(self, parent_id, row):
        id_list = self._get_id_list(parent_id)
        try:
            return id_list[row]
        except IndexError as x:
            raise KeyError(f"{x}: {parent_id} / {row} : {id_list}")

    def parent_id(self, id):
        if id == 0:
            return 0
        else:
            return self._id_to_parent_id[id]

    def has_children(self, id):
        return self.row_count(id) > 0

    def row_count(self, parent_id):
        id_list = self._get_id_list(parent_id)
        return len(id_list)

    def process_diff(self, diff):
        log.info("Tree adapter: process diff: %s", diff)
        if not isinstance(diff, (TreeDiff.Append, TreeDiff.Insert, TreeDiff.Replace, TreeDiff.Remove)):
            raise NotImplementedError(diff)
        visual_diff = self._apply_diff(diff)
        for subscriber in self._subscribers:
            subscriber.process_diff(visual_diff)

    def _append_item(self, parent_id, item):
        id_list = self._get_id_list(parent_id)
        item_id = next(self._id_counter)
        self._id_to_parent_id[item_id] = parent_id
        self._id_to_item[item_id] = item
        id_list.append(item_id)

    def _remove_item(self, parent_id, id_list, idx):
        item_id = id_list[idx]
        del id_list[idx]
        # Those dicts are still used by Qt for some time after removal.
        # TODO: Uncomment and wrap usages so that key absence be returned to Qt as proper missing/null index.
        # del self._id_to_item[item_id]
        # del self._id_to_parent_id[item_id]

    def get_item(self, id):
        return self._id_to_item.get(id)

    def get_path(self, id):
        path = []
        while id != 0:
            parent_id = self._id_to_parent_id[id]
            idx = self._id_to_children_id_list[parent_id].index(id)
            path.insert(0, idx)
            id = parent_id
        return path

    def path_to_item_id(self, path):
        item_id = 0
        idx = 0
        while idx < len(path):
            id_list = self._get_id_list(item_id)
            item_id = id_list[path[idx]]
            idx += 1
        return item_id

    def _get_id_list(self, parent_id):
        try:
            return self._id_to_children_id_list[parent_id]
        except KeyError:
            return self._populate(parent_id)

    def _populate(self, parent_id):
        item_list = self._retrieve_item_list(parent_id)
        log.info("Tree adapter: retrieved item list for %s/%s: %s", self._model, parent_id, item_list)
        id_list = []
        for item in item_list:
            id = next(self._id_counter)
            id_list.append(id)
            self._id_to_item[id] = item
            self._id_to_parent_id[id] = parent_id
        self._id_to_children_id_list[parent_id] = id_list
        return id_list

    @abc.abstractmethod
    def _retrieve_item_list(self, parent_id):
        pass


class FnTreeAdapterBase(TreeAdapterBase, metaclass=abc.ABCMeta):

    def __init__(self, feed_factory, model, item_t):
        super().__init__(model, item_t)
        self._column_names = sorted(self._item_t.fields)
        try:
            self._feed = feed_factory(model)
        except KeyError:
            self._feed = None
        else:
            self._feed.subscribe(self)

    def column_count(self):
        return len(self._column_names)

    def column_title(self, column):
        return self._column_names[column]

    def cell_data(self, id, column):
        item = self._id_to_item[id]
        return getattr(item, self._column_names[column])

    def _retrieve_item_list(self, parent_id):
        additional_kw = {
            'model': self._model,
            'piece': self._model,
            'feed': self._feed,
            **self._parent_model_kw(parent_id),
            }
        return self._call_fn(**additional_kw)

    @abc.abstractmethod
    def _call_fn(self, **kw):
        pass
