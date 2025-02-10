from hyperapp.boot.code_registry import CodeRegistry

from .services import (
    web,
    )


class ContextCodeRegistry(CodeRegistry):

    def __init__(self, service_name, config):
        super().__init__(web, service_name, config)

    def _call(self, fn, piece, args, kw):
        if len(args) != 1 or kw:
            raise RuntimeError(f"View registry expects single argument, 'ctx': {args!r} / {kw!r}")
        ctx = args[0]
        return fn.call(ctx, piece=piece)
