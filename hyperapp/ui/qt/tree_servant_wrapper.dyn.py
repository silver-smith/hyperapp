# Store servant wrapper to separate module to avoid unneeded dependencies.

import logging
from functools import partial

from .services import (
    pyobj_creg,
    )

log = logging.getLogger(__name__)


def index_tree_wrapper(servant_ref, grand_parent, is_lateral, lateral_parent, result_mt):
    result_t = pyobj_creg.animate(result_mt)
    servant = pyobj_creg.invite(servant_ref)
    parent = servant.keywords['parent']
    log.info("Index tree servant wrapper: Loading items for %s using %s", parent, servant)
    lateral_item_list_list = []
    if is_lateral:
        item_list = None
        log.info("Index tree servant wrapper: Loading siblings for %s, children for %s", lateral_parent, grand_parent)
        kw = {
            **servant.keywords,
            'parent': grand_parent,
            }
        lateral_parent_list = servant.func(**kw)
    else:
        item_list = tuple(servant())
        log.info("Index tree servant wrapper: Loading children for %s", lateral_parent)
        lateral_parent_list = item_list
    for item in lateral_parent_list:
        kw = {
            **servant.keywords,
            'parent': item,
            }
        items = servant.func(**kw)
        lateral_item_list_list.append(tuple(items))
    return result_t(item_list, tuple(lateral_item_list_list))


def key_tree_wrapper(servant_ref, key_field, is_lateral, result_mt):
    result_t = pyobj_creg.animate(result_mt)
    servant = pyobj_creg.invite(servant_ref)
    current_path = servant.keywords['current_path']
    log.info("Key tree servant wrapper: Loading items for %s using %s", current_path, servant)
    lateral_item_list_list = []
    if is_lateral:
        item_list = None
        parent_path = current_path[:-1]
        log.info("Key tree servant wrapper: Loading siblings for %s, children for %s", current_path, parent_path)
        kw = {
            **servant.keywords,
            'current_path': parent_path,
            }
        lateral_parent_list = servant.func(**kw)
    else:
        item_list = tuple(servant())
        parent_path = current_path
        log.info("Key tree servant wrapper: Loading children for %s", current_path)
        lateral_parent_list = item_list
    for item in lateral_parent_list:
        key = getattr(item, key_field)
        kw = {
            **servant.keywords,
            'current_path': (*parent_path, key),
            }
        items = servant.func(**kw)
        lateral_item_list_list.append(tuple(items))
    return result_t(item_list, tuple(lateral_item_list_list))
