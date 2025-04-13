# Store servant wrapper to separate module to avoid unneeded dependencies.

import logging
from functools import partial

from .services import (
    pyobj_creg,
    )
from .code.context import Context

log = logging.getLogger(__name__)


def index_tree_wrapper(servant_fn_piece, model, parent, grand_parent, is_lateral, lateral_parent, result_mt, system_fn_creg):
    result_t = pyobj_creg.animate(result_mt)
    servant_fn = system_fn_creg.animate(servant_fn_piece)
    log.info("Index tree servant wrapper: Loading items for %s using %s", parent, servant_fn)
    ctx = Context(
        model=model,
        piece=model,
        )
    lateral_item_list_list = []
    if is_lateral:
        item_list = None
        log.info("Index tree servant wrapper: Loading siblings for %s, children for %s", lateral_parent, grand_parent)
        lateral_parent_list = servant_fn.call(ctx, parent=grand_parent)
    else:
        item_list = tuple(servant_fn.call(ctx, parent=parent))
        log.info("Index tree servant wrapper: Loading children for %s", lateral_parent)
        lateral_parent_list = item_list
    for item in lateral_parent_list:
        items = servant_fn.call(ctx, parent=item)
        lateral_item_list_list.append(tuple(items))
    return result_t(item_list, tuple(lateral_item_list_list))


def key_tree_wrapper(servant_fn_piece, model, current_path, key_field, is_lateral, result_mt, system_fn_creg):
    result_t = pyobj_creg.animate(result_mt)
    servant_fn = system_fn_creg.animate(servant_fn_piece)
    log.info("Key tree servant wrapper: Loading items for %s using %s", current_path, servant_fn)
    ctx = Context(
        model=model,
        piece=model,
        )
    lateral_item_list_list = []
    if is_lateral:
        item_list = None
        parent_path = current_path[:-1]
        log.info("Key tree servant wrapper: Loading siblings for %s, children for %s", current_path, parent_path)
        lateral_parent_list = servant_fn.call(ctx, current_path=parent_path)
    else:
        item_list = tuple(servant_fn.call(ctx, current_path=current_path))
        log.info("Key tree servant wrapper: Loading children for %s", current_path)
        parent_path = current_path
        lateral_parent_list = item_list
    for item in lateral_parent_list:
        key = getattr(item, key_field)
        items = servant_fn.call(ctx, current_path=(*parent_path, key))
        lateral_item_list_list.append(tuple(items))
    return result_t(item_list, tuple(lateral_item_list_list))
