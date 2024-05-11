from . import htypes
from .services import (
    constructor_creg,
    )


@constructor_creg.actor(htypes.rc_constructors.model_ctr)
def construct(piece, custom_types, name_to_res, module_res, attr):
    pass
