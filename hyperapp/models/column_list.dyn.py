from hyperapp.common.htypes import TList

from . import htypes
from .services import (
    deduce_t,
    pyobj_creg,
    )
from .code.mark import mark


@mark.model
def column_list(piece, lcs):
    item_t = pyobj_creg.invite(piece.item_t)
    item_list = []
    for name in item_t.fields:
        item = htypes.column_list.item(
            name=name,
            show=True,
            )
        item_list.append(item)
    return item_list


@mark.ui_model_command(htypes.list.view)
def open_column_list(view):
    model_t = deduce_t(view.adapter.model)
    if isinstance(model_t, TList):
        return
    return htypes.column_list.view(
        model_t=pyobj_creg.actor_to_ref(model_t),
        item_t=pyobj_creg.actor_to_ref(view.adapter.item_t),
        )
