from .services import (
    pyobj_creg,
    )
from .code.mark import mark


@mark.actor.resource_name_creg
def column_k_resource_name(piece, gen):
    model_t = pyobj_creg.invite(piece.model_t)
    return f'column_k-{model_t.full_name}-{piece.column_name}'
