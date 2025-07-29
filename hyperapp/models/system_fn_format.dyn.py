from .services import (
    web,
    )
from .code.mark import mark


@mark.actor.formatter_creg
def format_ctx_fn(piece, format):
    fn = web.summon(piece.function)
    fn_title = format(fn)
    return f"ctx_fn({fn_title}, ctx_params={piece.ctx_params}, service_params={piece.service_params})"
