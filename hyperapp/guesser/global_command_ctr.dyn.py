import re

from . import htypes
from .services import (
    constructor_creg,
    mosaic,
    types,
  )


# https://stackoverflow.com/a/1176023 Camel case to snake case.
def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


@constructor_creg.actor(htypes.global_command_ctr.global_command_ctr)
def construct(piece, custom_types, resource_module, module_res, attr):
    dir_name = camel_to_snake(attr.name) + '_d'
    dir_t_ref = custom_types[resource_module.name][dir_name]
    dir_t = types.resolve(dir_t_ref)
    dir = dir_t()
    resource_module[dir_name] = dir

    attribute = htypes.attribute.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    resource_module[attr.name] = attribute

    command = htypes.impl.global_command_impl(
        function=mosaic.put(attribute),
        dir=mosaic.put(dir),
        )
    resource_module[f'{attr.name}.command'] = command

    association = htypes.global_command.global_command_association(
        command=mosaic.put(command),
        )
    resource_module.add_association(association)
