import abc
import logging
import weakref
from functools import cached_property

from hyperapp.common.htypes import tInt, TOptional, TRecord

from .code.list_diff import ListDiff

log = logging.getLogger(__name__)


class ListAdapterBase:

    @cached_property
    def model_state_t(self):
        item_t = self._item_t
        return TRecord('ui_list', f'model_state_{item_t.module_name}_{item_t.name}', {
            'current_idx': tInt,
            'current_item': TOptional(item_t),
            })


class FnListAdapterBase(ListAdapterBase, metaclass=abc.ABCMeta):

    def __init__(self, feed_factory, model, item_t, params, ctx):
        self._model = model
        self._item_t = item_t
        self._params = params
        self._ctx = ctx
        self._column_names = sorted(self._item_t.fields)
        self._item_list = None
        self._subscribers = weakref.WeakSet()
        try:
            self._feed = feed_factory(model)
        except KeyError:
            self._feed = None
        else:
            self._feed.subscribe(self)

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    @property
    def model(self):
        return self._model

    def column_count(self):
        return len(self._item_t.fields)

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
        else:
            raise NotImplementedError(diff)
        for subscriber in self._subscribers:
            subscriber.process_diff(diff)

    @property
    def element_t(self):
        return self._item_t

    @property
    def function_params(self):
        return self._params

    @property
    def _items(self):
        if self._item_list is not None:
            return self._item_list
        self._populate()
        return self._item_list

    def _populate(self):
        available_params = {
            **self._ctx.as_dict(),
            'piece': self._model,
            'feed': self._feed,
            'ctx': self._ctx,
            }
        kw = {
            name: available_params[name]
            for name in self._params
            }
        self._item_list = self._call_fn(**kw)

    @abc.abstractmethod
    def _call_fn(self, **kw):
        pass
