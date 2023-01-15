from . import htypes
from .services import (
    mosaic,
    )


def construct(piece, custom_types, resource_module, module_res, attr):
    attribute = htypes.attribute.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    resource_module[attr.name] = attribute
    association = htypes.code_registry.association(
        service=piece.service,
        type=piece.type,
        function=mosaic.put(attribute),
        )
    resource_module.add_association(association)
