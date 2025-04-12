from .code.mark import mark


@mark.service
def error_view(view_reg, visualizer, exception, ctx):
    model = str(exception)
    view_piece = visualizer(ctx, model)
    model_ctx = ctx.clone_with(model=model)
    view = view_reg.animate(view_piece, model_ctx)
    return (model, view)
