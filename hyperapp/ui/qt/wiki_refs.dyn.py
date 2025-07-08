import logging
import weakref

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.value_diff import SetValueDiff

log = logging.getLogger(__name__)


class WikiRefListAdapter:

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx, format, accessor_creg):
        accessor = accessor_creg.invite(piece.accessor, model, ctx)
        return cls(format, accessor)

    def __init__(self, format, accessor):
        self._format = format
        self._accessor = accessor
        self._column_names = ['id', 'target', 'title']
        self._subscribers = weakref.WeakSet()
        self._accessor.subscribe(self)

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    def column_count(self):
        return len(self._column_names)

    def column_title(self, column):
        return self._column_names[column]

    def row_count(self):
        return len(self._ref_list)

    def cell_data(self, row, column):
        item = self.get_item(row)
        return getattr(item, self._column_names[column])

    def make_model_state(self, current_idx, current_item):
        return htypes.wiki.ref_list_model_state(
            current_id=current_item.id,
            current_item=current_item,
            )

    def get_item(self, idx):
        rec = self._ref_list[idx]
        target = web.summon(rec.target)
        title = self._format(target)
        return htypes.wiki.ref_list_item(
            id=rec.id,
            target=rec.target,
            title=title,
            )

    def value_changed(self, new_value):
        log.info("Wiki ref list adapter: value changed: %r", new_value)
        visual_diff = SetValueDiff(new_value)
        for subscriber in self._subscribers:
            subscriber.process_diff(visual_diff)


    @property
    def _ref_list(self):
        return self._accessor.get_value().refs


@mark.view_factory.model_t(htypes.wiki.wiki)
def wiki_refs(accessor):
    adapter = htypes.wiki.ref_list_adapter(
        accessor=mosaic.put(accessor),
        )
    return htypes.list.view(
        adapter=mosaic.put(adapter),
        )
