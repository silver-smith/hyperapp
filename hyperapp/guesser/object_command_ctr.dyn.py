from . import htypes
from .services import (
    constructor_creg,
    mosaic,
    types,
  )
from .code.utils import camel_to_snake


@constructor_creg.actor(htypes.object_command_ctr.object_command_ctr)
def construct(piece, custom_types, name_to_res, module_res, attr):
    dir_name = camel_to_snake(attr.name) + '_d'
    dir_t_ref = custom_types[name_to_res.name][dir_name]
    dir_t = types.resolve(dir_t_ref)
    dir = dir_t()
    name_to_res[dir_name] = dir

    attribute = htypes.attribute.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    name_to_res[attr.name] = attribute

    command = htypes.impl.object_command_impl(
        function=mosaic.put(attribute),
        params=attr.param_list,
        dir=mosaic.put(dir),
        )
    name_to_res[f'{attr.name}.command'] = command

    # Called for every command, but results with single resource.
    object_commands_d = htypes.command.object_commands_d()
    name_to_res['object_commands_d'] = object_commands_d

    association = htypes.lcs.lcs_set_association(
        dir=(mosaic.put(object_commands_d),),
        value=mosaic.put(command),
        )
    return [association]
