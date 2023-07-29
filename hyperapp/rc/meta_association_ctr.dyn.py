from hyperapp.common.htypes.meta_association import meta_association_t

from . import htypes
from .services import (
    constructor_creg,
    mark,
    mosaic,
    )


@constructor_creg.actor(htypes.attr_constructors.meta_association)
def construct(piece, custom_types, name_to_res, module_res, attr):
    attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    ass = meta_association_t(
        t=piece.type,
        fn=mosaic.put(attribute),
        )
    name_to_res[attr.name] = attribute
    return [ass]
