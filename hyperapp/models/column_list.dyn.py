from hyperapp.common.htypes import TList

from . import htypes
from .services import (
    deduce_t,
    pyobj_creg,
    )
from .code.mark import mark


def _column_d(model_t, name):
    return {
        htypes.column.list_d(),
        pyobj_creg.actor_to_piece(model_t),
        htypes.column.column_d(name),
        }


@mark.model
def column_list(piece, lcs):
    model_t = pyobj_creg.invite(piece.model_t)
    item_t = pyobj_creg.invite(piece.item_t)
    item_list = []
    for name in item_t.fields:
        d = _column_d(model_t, name)
        show_d = d | {htypes.column.show_d()}
        item = htypes.column_list.item(
            name=name,
            show=lcs.get(show_d, True),
            )
        item_list.append(item)
    return item_list


@mark.command
def toggle_visibility(piece, current_item, lcs):
    model_t = pyobj_creg.invite(piece.model_t)
    key = _column_d(model_t, current_item.name) | {htypes.column.show_d()}
    prev_value = lcs.get(key, True)
    lcs.set(key, not prev_value)


@mark.ui_model_command(htypes.list.view)
def open_column_list(view):
    model_t = deduce_t(view.adapter.model)
    if isinstance(model_t, TList):
        return
    return htypes.column_list.view(
        model_t=pyobj_creg.actor_to_ref(model_t),
        item_t=pyobj_creg.actor_to_ref(view.adapter.item_t),
        )
