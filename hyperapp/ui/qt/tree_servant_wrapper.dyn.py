# Store servant wrapper to separate module to avoid unneeded dependencies.

import logging
from functools import partial

from .services import (
    pyobj_creg,
    )

log = logging.getLogger(__name__)


def index_tree_wrapper(servant_ref):
    servant = pyobj_creg.invite(servant_ref)
    item_list = servant()
    return (tuple(item_list), ())


def key_tree_wrapper(servant_ref, key_field, is_lateral, result_mt):
    result_t = pyobj_creg.animate(result_mt)
    sub_rec_t = result_t.fields['sub_rec_list'].element_t
    servant = pyobj_creg.invite(servant_ref)
    current_path = servant.keywords['current_path']
    log.info("Tree servent wrapper: Loading items for %s", current_path)
    item_list = servant()
    sub_rec_list = []
    if is_lateral:
        parent_path = current_path[:-1]
        log.info("Tree servent wrapper: Loading siblings for %s", parent_path)
        kw = {
            **servant.keywords,
            'current_path': parent_path,
            }
        sub_item_list = servant.func(**kw)
    else:
        log.info("Tree servent wrapper: Loading children for %s", current_path)
        sub_item_list = item_list
        parent_path = current_path
    for item in sub_item_list:
        key = getattr(item, key_field)
        kw = {
            **servant.keywords,
            'current_path': (*parent_path, key),
            }
        items = servant.func(**kw)
        rec = sub_rec_t(key, tuple(items))
        sub_rec_list.append(rec)
    return result_t(tuple(item_list), tuple(sub_rec_list))
        
