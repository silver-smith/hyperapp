from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.wrapper_view import WrapperView


class TreeAsListWrapperView(WrapperView):

    @classmethod
    @mark.view
    def from_piece(cls, piece, model, ctx, view_reg, system_fn_creg):
        list_model = htypes.tree_as_list.list_model(
            tree_model=mosaic.put(model),
            tree_model_fn=piece.tree_model_fn,
            current_path=(),
            parent_item=None,
            )
        list_ctx = ctx.clone_with(
            model=list_model,
            piece=list_model,
            )
        list_view = view_reg.invite(piece.list_view, list_ctx)
        tree_model_fn = system_fn_creg.invite(piece.tree_model_fn)
        return cls(list_view, tree_model_fn)

    def __init__(self, list_view, tree_model_fn):
        super().__init__(list_view)
        self._tree_model_fn = tree_model_fn

    @property
    def piece(self):
        return htypes.tree_as_list.view(
            list_view=mosaic.put(self._base_view.piece),
            tree_model_fn=mosaic.put(self._tree_model_fn.piece),
            current_path=(),
            )


def list_model_fn(piece, current_idx, ctx, system_fn_creg):
    tree_model = web.summon(piece.tree_model)
    tree_model_fn = system_fn_creg.invite(piece.tree_model_fn)
    current_path = [web.summon(idx) for idx in piece.current_path]
    parent_item = web.summon_opt(piece.parent_item)
    tree_ctx = ctx.clone_with(
        model=tree_model,
        piece=tree_model,
        current_path=(*current_path, current_idx),
        parent=parent_item,
        )
    return tree_model_fn.call(tree_ctx)


@mark.view_factory.ui_t
def index_tree_as_list_ui_type_layout(piece, system_fn_ref):
    list_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(list_model_fn),
        ctx_params=('piece', 'current_idx', 'ctx'),
        service_params=('system_fn_creg',),
        )
    list_adapter = htypes.list_adapter.index_fn_list_adapter(
        item_t=piece.item_t,
        system_fn=mosaic.put(list_fn),
        )
    list_view = htypes.list.view(
        adapter=mosaic.put(list_adapter),
        )
    return htypes.tree_as_list.view(
        list_view=mosaic.put(list_view),
        tree_model_fn=system_fn_ref,
        current_path=(),
        )
