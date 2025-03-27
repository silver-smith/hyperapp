import inspect

from .code.mark import mark


class UnboundArgsPickerCommandEnumerator:

    @classmethod
    @mark.actor.command_creg
    def from_piece(cls, piece, system_fn_creg):
        commit_fn = system_fn_creg.invite(piece.commit_fn)
        return cls(
            commit_fn=commit_fn,
            )

    def __init__(self, commit_fn):
        self._commit_fn = commit_fn

    def __repr__(self):
        return f"<ArgsPickerCommandEnum: {self._commit_fn}>"

    def enum_commands(self, ctx):
        # log.info("Run command enumerator: %r (%s)", self, kw)
        result = self._commit_fn.call(ctx)
        assert not inspect.iscoroutine(result), f"Async command enumerators are not supported: {self._commit_fn}"
        log.info("Run command enumerator %r result: [%s] %r", self, type(result), result)
        return result
