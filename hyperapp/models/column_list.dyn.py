from hyperapp.boot.htypes import TList

from . import htypes
from .services import (
    deduce_t,
    pyobj_creg,
    )
from .code.mark import mark
from .code.list_diff import IndexListDiff


def _column_key(model_t, name):
    return htypes.column.column_k(
        model_t=pyobj_creg.actor_to_ref(model_t),
        column_name=name,
        )


def _item(column_visible_reg, model_t, name):
    key = _column_key(model_t, name)
    return htypes.column_list.item(
        name=name,
        show=column_visible_reg.get(key, True),
        )


@mark.model
def column_list(piece, column_visible_reg):
    model_t = pyobj_creg.invite(piece.model_t)
    item_t = pyobj_creg.invite(piece.item_t)
    return [
        _item(column_visible_reg, model_t, name)
        for name in item_t.fields
        ]


@mark.command
async def toggle_visibility(piece, current_idx, current_item, feed_factory, column_visible_reg):
    feed = feed_factory(piece)
    model_t = pyobj_creg.invite(piece.model_t)
    key = _column_key(model_t, current_item.name)
    prev_value = column_visible_reg.get(key, True)
    column_visible_reg[key] = not prev_value
    item = _item(column_visible_reg, model_t, current_item.name)
    await feed.send(IndexListDiff.Replace(current_idx, item))


@mark.ui_model_command(htypes.list.view)
def open_column_list(view):
    model_t = deduce_t(view.adapter.model)
    if isinstance(model_t, TList):
        return
    return htypes.column_list.view(
        model_t=pyobj_creg.actor_to_ref(model_t),
        item_t=pyobj_creg.actor_to_ref(view.adapter.item_t),
        )
