from .services import (
    pyobj_creg,
    )
from .code.mark import mark


@mark.actor.formatter_creg
def format_column(piece):
    model_t = pyobj_creg.invite(piece.model_t)
    return f"column_k({model_t.full_name}:{piece.column_name})"
