from hyperapp.common.code_registry import CodeRegistry

from .services import (
    code_registry_ctr,
    web,
    )
from .code.mark import mark


class ViewCodeRegistry(CodeRegistry):

    def __init__(self, config):
        super().__init__(web, 'view_reg', config)

    def _call(self, fn, piece, args, kw):
        if len(args) != 1 or kw:
            raise RuntimeError(f"View registry expects single argument, 'ctx': {args!r} / {kw!r}")
        ctx = args[0]
        return fn.call(ctx, piece=piece)


@mark.service
def view_creg(config):
    return code_registry_ctr('view_creg', config)


@mark.service
def model_view_creg(config):
    return code_registry_ctr('model_view_creg', config)


@mark.service
def view_reg(config):
    return ViewCodeRegistry(config)
