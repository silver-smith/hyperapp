from hyperapp.common.association_registry import Association

from . import htypes
from .services import (
    constructor_creg,
    mosaic,
    pyobj_creg,
    types,
    web,
  )
from .code.utils import camel_to_snake


@constructor_creg.actor(htypes.attr_constructors.ui_command_ctr)
def construct(piece, custom_types, name_to_res, module_res, attr):
    dir_t_res = pyobj_creg.reverse_resolve(htypes.ui.ui_command_d)
    dir_res = htypes.builtin.call(
        function=mosaic.put(dir_t_res),
        )
    t_res = web.summon(piece.t)
    attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    association = Association(
        bases=[
            dir_t_res,
            t_res,
            ],
        key=[
            dir_t_res,
            t_res,
            ],
        value=attribute,
        )
    name_to_res['ui_command_d'] = dir_res
    name_to_res[attr.name] = attribute
    return [association]

