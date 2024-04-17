from hyperapp.common.association_registry import Association

from . import htypes
from .services import (
    constructor_creg,
    data_to_res,
    pyobj_creg,
    web,
  )


@constructor_creg.actor(htypes.rc_constructors.list_feed_ctr)
def construct_list_feed(piece, custom_types, name_to_res, module_res):
    dir_res = data_to_res(htypes.ui.feed_d())
    t_res = web.summon(piece.t)
    feed = htypes.ui.list_feed(
        element_t=piece.element_t,
        )
    association = Association(
        bases=[dir_res, t_res],
        key=[dir_res, t_res],
        value=feed,
        )
    piece_t = pyobj_creg.invite(piece.t)
    name_to_res['feed_d'] = dir_res
    name_to_res[f'{piece_t.module_name}_{piece_t.name}.list_feed'] = feed
    return [association]
