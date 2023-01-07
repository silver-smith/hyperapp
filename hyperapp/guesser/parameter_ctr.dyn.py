from . import htypes
from .services import (
    mark,
    mosaic,
    )


def construct(piece, custom_types, resource_module, module_res, attr):
    attribute = htypes.attribute.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    resource_module[attr.name] = attribute
    parameter = htypes.call.call(
        function=mosaic.put(attribute),
        )
    resource_module['.'.join(piece.path)] = parameter
