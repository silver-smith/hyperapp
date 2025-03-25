from .code.mark import mark


class UnboundArgsPickerCommandEnumerator:

    def __init__(self, ctx_fn):
        self._ctx_fn = ctx_fn

    def __repr__(self):
        return f"<ArgsPickerCommandEnum: {self._ctx_fn}>"

    def enum_commands(self, ctx):
        # log.info("Run command enumerator: %r (%s)", self, kw)
        result = self._ctx_fn.call(ctx)
        assert not inspect.iscoroutine(result), f"Async command enumerators are not supported: {self._ctx_fn}"
        log.info("Run command enumerator %r result: [%s] %r", self, type(result), result)
        return result


@mark.actor.command_creg
def args_picker_command_enumerator_from_piece(piece, system_fn_creg):
    ctx_fn = system_fn_creg.invite(piece.system_fn)
    return UnboundArgsPickerCommandEnumerator(
        ctx_fn=ctx_fn,
        )
