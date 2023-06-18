from . import htypes
from .services import (
    constructor_creg,
    mosaic,
    types,
  )
from .code.utils import camel_to_snake


@constructor_creg.actor(htypes.global_command_ctr.global_command_ctr)
def construct(piece, custom_types, name_to_res, module_res, attr):
    dir_name = camel_to_snake(attr.name) + '_d'
    dir_t_ref = custom_types[name_to_res.name][dir_name]
    dir_t = types.resolve(dir_t_ref)
    dir = dir_t()
    name_to_res[dir_name] = dir

    attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    name_to_res[attr.name] = attribute

    command = htypes.impl.global_command_impl(
        function=mosaic.put(attribute),
        dir=mosaic.put(dir),
        )
    name_to_res[f'{attr.name}.command'] = command

    association = htypes.global_command.global_command_association(
        command=mosaic.put(command),
        )
    return [association]
