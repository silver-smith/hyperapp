from .services import (
    web,
    )
from .code.mark import mark


@mark.universal_ui_command(args=['view_factory'])
def wrap_view(view_factory, view, hook, ctx, view_reg, view_factory_reg):
    k = web.summon(view_factory.k)
    factory = view_factory_reg[k]
    fn_ctx = ctx.clone_with(
        inner=view.piece,
        )
    view_piece = factory.fn.call(ctx=fn_ctx)
    new_view = view_reg.animate(view_piece, ctx)
    hook.replace_view(new_view)
