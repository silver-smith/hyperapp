from hyperapp.common.association_registry import Association

from . import htypes
from .services import (
    constructor_creg,
    data_to_res,
    mosaic,
    pyobj_creg,
    types,
    web,
  )
from .code.utils import camel_to_snake


@constructor_creg.actor(htypes.attr_constructors.ui_command_ctr)
def construct_ui_command(piece, custom_types, name_to_res, module_res, attr):
    dir_res = data_to_res(htypes.ui.ui_command_d())
    t_res = web.summon(piece.t)
    attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    association = Association(
        bases=[dir_res, t_res],
        key=[dir_res, t_res],
        value=attribute,
        )
    name_to_res['ui_command_d'] = dir_res
    name_to_res[attr.name] = attribute
    return [association]


@constructor_creg.actor(htypes.attr_constructors.universal_ui_command_ctr)
def construct_universal_ui_command(piece, custom_types, name_to_res, module_res, attr):
    dir_res = data_to_res(htypes.ui.universal_ui_command_d())
    attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    association = Association(
        bases=[dir_res],
        key=[dir_res],
        value=attribute,
        )
    name_to_res['universal_ui_command_d'] = dir_res
    name_to_res[attr.name] = attribute
    return [association]

