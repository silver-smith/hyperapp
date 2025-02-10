from .services import (
    web,
    )
from .code.mark import mark


@mark.universal_ui_command(args=['view_factory'])
def wrap_view(view_factory, view, ctx, view_factory_reg):
    d = web.summon(view_factory.d)
    factory = view_factory_reg[d]
    fn_ctx = ctx.clone_with(
        inner=view.piece,
        )
    return factory.fn.call(ctx=fn_ctx)
