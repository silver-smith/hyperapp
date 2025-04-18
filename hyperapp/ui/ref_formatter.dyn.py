from .services import (
    web,
    )
from .code.mark import mark


@mark.actor.formatter_creg
def format_ref(piece, format):
    target_piece = web.summon(piece)
    return format(target_piece)
