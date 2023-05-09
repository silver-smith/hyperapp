from . import htypes
from .services import (
    constructor_creg,
    mark,
    mosaic,
    )


@constructor_creg.actor(htypes.attr_constructors.service)
def construct(piece, custom_types, name_to_res, module_res, attr):
    attribute = htypes.attribute.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    name_to_res[attr.name] = attribute
    service = htypes.call.call(
        function=mosaic.put(attribute),
        )
    name_to_res[f'{piece.name}.service'] = service
