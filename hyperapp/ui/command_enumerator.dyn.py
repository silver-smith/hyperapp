import inspect
import logging

log = logging.getLogger(__name__)


class UnboundCommandEnumerator:

    def __init__(self, ctx_fn):
        self._ctx_fn = ctx_fn

    def __repr__(self):
        return f"<CommandEnum: {self._ctx_fn}>"

    def enum_commands(self, ctx):
        # log.info("Run command enumerator: %r (%s)", self, kw)
        result = self._ctx_fn.call(ctx)
        assert not inspect.iscoroutine(result), f"Async command enumerators are not supported: {self._ctx_fn}"
        log.info("Run command enumerator %r result: [%s] %r", self, type(result), result)
        return result
