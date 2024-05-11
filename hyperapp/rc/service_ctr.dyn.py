from . import htypes
from .services import (
    constructor_creg,
    mosaic,
    )


@constructor_creg.actor(htypes.rc_constructors.service)
def construct(piece, custom_types, name_to_res, module_res, attr):
    attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    name_to_res[attr.name] = attribute
    service = htypes.builtin.call(
        function=mosaic.put(attribute),
        )
    name_to_res[f'{piece.name}.service'] = service
