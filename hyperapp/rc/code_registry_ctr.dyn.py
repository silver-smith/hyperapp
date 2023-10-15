from hyperapp.common.association_registry import Association

from . import htypes
from .services import (
    mosaic,
    web,
    )


def construct(piece, custom_types, name_to_res, module_res, attr):
    attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    association = Association(
        bases=[
            web.summon(piece.service), 
            web.summon(piece.type),
            ],
        key=[
            web.summon(piece.service),
            web.summon(piece.type),
            ],
        value=attribute,
        )
    name_to_res[attr.name] = attribute
    return [association]
