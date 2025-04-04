import abc
import logging
import weakref
from functools import cached_property

from hyperapp.boot.htypes import tInt, TOptional, TRecord

from . import htypes
from .services import (
    deduce_t,
    pyobj_creg,
    )
from .code.list_diff import ListDiff

log = logging.getLogger(__name__)


def index_list_model_state_t(item_t):
    return TRecord('ui_list', f'list_model_state_{item_t.module_name}_{item_t.name}', {
        'current_idx': tInt,
        'current_item': TOptional(item_t),
        })


def key_list_model_state_t(item_t, key_field, key_field_t):
    return TRecord('ui_list', f'list_model_state_{item_t.module_name}_{item_t.name}', {
        'current_key': key_field_t,
        f'current_{key_field}': key_field_t,
        'current_item': TOptional(item_t),
        })


class IndexListAdapterMixin:

    @cached_property
    def model_state_t(self):
        return index_list_model_state_t(self._item_t)

    def make_model_state(self, current_idx, current_item):
        return self.model_state_t(
            current_idx=current_idx,
            current_item=current_item,
            )


class KeyListAdapterMixin:

    def __init__(self, key_field, key_field_t):
        self._key_field = key_field
        self._key_field_t = key_field_t

    @cached_property
    def model_state_t(self):
        return key_list_model_state_t(self._item_t, self._key_field, self._key_field_t)

    def make_model_state(self, current_idx, current_item):
        current_key = getattr(current_item, self._key_field)
        return self.model_state_t(
            current_key=current_key,
            current_item=current_item,
            **{f'current_{self._key_field}': current_key},
            )


class FnListAdapterBase(metaclass=abc.ABCMeta):

    def __init__(self, feed_factory, column_visible_reg, model, item_t):
        self._column_visible_reg = column_visible_reg
        self._model = model
        self._model_t = deduce_t(model)
        self._item_t = item_t
        self._column_names = sorted(filter(self._column_visible, self._item_t.fields))
        self._item_list = None
        self._subscribers = weakref.WeakSet()
        try:
            self._feed = feed_factory(model)
        except KeyError:
            self._feed = None
        else:
            self._feed.subscribe(self)

    def _column_k(self, name):
        return htypes.column.column_k(
            model_t=pyobj_creg.actor_to_ref(self._model_t),
            column_name=name,
            )

    def _column_visible(self, name):
        key = self._column_k(name)
        return self._column_visible_reg.get(key, True)

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    @property
    def model(self):
        return self._model

    def column_count(self):
        return len(self._column_names)

    def column_title(self, column):
        return self._column_names[column]

    def row_count(self):
        return len(self._items)

    def cell_data(self, row, column):
        item = self._items[row]
        return getattr(item, self._column_names[column])

    def get_item(self, idx):
        return self._items[idx]

    def process_diff(self, diff):
        log.info("List adapter: process diff: %s", diff)
        if self._item_list is None:
            self._populate()
        if isinstance(diff, ListDiff.Append):
            self._item_list.append(diff.item)
        elif isinstance(diff, ListDiff.Replace):
            self._item_list[diff.idx] = diff.item
        elif isinstance(diff, ListDiff.Remove):
            del self._item_list[diff.idx]
        else:
            raise NotImplementedError(diff)
        for subscriber in self._subscribers:
            subscriber.process_diff(diff)

    @property
    def item_t(self):
        return self._item_t

    @property
    def _items(self):
        if self._item_list is not None:
            return self._item_list
        self._populate()
        return self._item_list

    def _populate(self):
        additional_kw = {
            'model': self._model,
            'piece': self._model,
            'feed': self._feed,
            }
        self._item_list = self._call_fn(**additional_kw)

    @abc.abstractmethod
    def _call_fn(self, **kw):
        pass
