from .services import (
    web,
    )
from .code.mark import mark


@mark.actor.formatter_creg
def format_rpc_request(piece, format):
    target = web.summon(piece.target)
    target_title = format(target)
    return f"rpc.request: {piece.request_id[-6:]}, {target_title}"


@mark.actor.formatter_creg
def format_rpc_response(piece, format):
    result = web.summon(piece.result_ref)
    result_title = format(result)
    return f"rpc.response: {piece.request_id[-6:]}, {result_title}"


@mark.actor.formatter_creg
def format_rpc_error_response(piece, format):
    exception = web.summon(piece.exception_ref)
    exception_title = format(exception)
    return f"rpc.response: {piece.request_id[-6:]}, {exception_title}"


@mark.actor.formatter_creg
def format_rpc_function_target(piece, format):
    servant = web.summon(piece.servant_ref)
    servant_title = format(servant)
    params = {
        p.name: format(web.summon(p.value))
        for p in piece.params
        }
    params_text = ', '.join(
        f"{name}: {value}"
        for name, value in params.items()
        )
    return f"fn: {servant_title}({params_text})"


@mark.actor.formatter_creg
def format_rpc_system_fn_target(piece, format):
    fn = web.summon(piece.fn)
    fn_title = format(fn)
    params = {
        p.name: format(web.summon(p.value))
        for p in piece.params
        }
    params_text = ', '.join(
        f"{name}: {value}"
        for name, value in params.items()
        )
    return f"fn: {fn_title}({params_text})"
