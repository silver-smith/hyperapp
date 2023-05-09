from . import htypes
from .services import (
    mosaic,
    )


def construct(piece, custom_types, name_to_res, module_res, attr):
    attribute = htypes.attribute.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    name_to_res[attr.name] = attribute
    association = htypes.code_registry.association(
        service=piece.service,
        type=piece.type,
        function=mosaic.put(attribute),
        )
    return [association]
