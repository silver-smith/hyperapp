# Store servant wrapper to separate module to avoid unneeded dependencies.

from functools import partial

from .services import (
    pyobj_creg,
    )


def index_tree_wrapper(servant_ref):
    servant = pyobj_creg.invite(servant_ref)
    item_list = servant()
    return (tuple(item_list), ())


def key_tree_wrapper(servant_ref, key_field, result_mt):
    result_t = pyobj_creg.animate(result_mt)
    sub_rec_t = result_t.fields['sub_rec_list'].element_t
    servant = pyobj_creg.invite(servant_ref)
    current_path = servant.keywords['current_path']
    item_list = servant()
    sub_rec_list = []
    for item in item_list:
        key = getattr(item, key_field)
        kw = {
            **servant.keywords,
            'current_path': (*current_path, key),
            }
        items = servant.func(**kw)
        rec = sub_rec_t(key, tuple(items))
        sub_rec_list.append(rec)
    return result_t(tuple(item_list), tuple(sub_rec_list))
        
