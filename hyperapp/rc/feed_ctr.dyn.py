from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.association_registry import Association

from . import htypes
from .services import (
    constructor_creg,
    data_to_res,
    pyobj_creg,
  )


@constructor_creg.actor(htypes.rc_constructors.list_feed_ctr)
def construct_list_feed(piece, custom_types, name_to_res, module_res):
    dir_res = data_to_res(htypes.ui.feed_d())
    piece_t = deduce_value_type(piece)
    t_res = pyobj_creg.reverse_resolve(piece_t)
    element_t = pyobj_creg.invite(piece.element_t)
    feed = htypes.ui.list_feed(
        element_t=piece.element_t,
        )
    association = Association(
        bases=[dir_res, t_res],
        key=[dir_res, t_res],
        value=feed,
        )
    name_to_res['feed_d'] = dir_res
    name_to_res[f'{element_t.module_name}_{element_t.name}.list_feed'] = feed
    return [association]
