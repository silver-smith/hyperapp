import logging

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.wrapper_view import WrapperView

log = logging.getLogger(__name__)


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
        current_path = [web.summon(elt) for elt in piece.current_path]
        return cls(list_view, tree_model_fn, list_model, current_path)

    def __init__(self, list_view, tree_model_fn, list_model, current_path):
        super().__init__(list_view)
        self._tree_model_fn = tree_model_fn
        self._list_model = list_model
        self._current_path = current_path

    @property
    def piece(self):
        return htypes.tree_as_list.view(
            list_view=mosaic.put(self._base_view.piece),
            tree_model_fn=mosaic.put(self._tree_model_fn.piece),
            current_path=tuple(mosaic.put(elt) for elt in self._current_path),
            )

    def children_context(self, ctx):
        return ctx.clone_with(model=self._list_model)

    def element_view(self, view_reg, ctx, tree_model, current_elt, current_item):
        return self._wrapper_view(view_reg, ctx, tree_model, [*self._current_path, current_elt], current_item)

    def parent_view(self, view_reg):
        if not self._current_path:
            return None
        return self._wrapper_view(self._current_path[:-1])

    def _wrapper_view(self, view_reg, ctx, tree_model, current_path, parent_item):
        list_model = htypes.tree_as_list.list_model(
            tree_model=mosaic.put(tree_model),
            tree_model_fn=mosaic.put(self._tree_model_fn.piece),
            current_path=tuple(mosaic.put(elt) for elt in current_path),
            parent_item=mosaic.put(parent_item),
            )
        list_ctx = ctx.clone_with(
            model=list_model,
            piece=list_model,
            )
        list_view = view_reg.animate(self._base_view.piece, list_ctx)
        return TreeAsListWrapperView(
            list_view=list_view,
            tree_model_fn=self._tree_model_fn,
            list_model=list_model,
            current_path=current_path,
            )


def list_model_fn(piece, ctx, system_fn_creg):
    tree_model = web.summon(piece.tree_model)
    tree_model_fn = system_fn_creg.invite(piece.tree_model_fn)
    current_path = tuple(web.summon(idx) for idx in piece.current_path)
    parent_item = web.summon_opt(piece.parent_item)
    tree_ctx = ctx.clone_with(
        model=tree_model,
        piece=tree_model,
        current_path=current_path,
        parent=parent_item,
        )
    log.info("Tree-as-list model: current_path=%s, parent=%s", current_path, parent_item)
    return tree_model_fn.call(tree_ctx)


@mark.ui_command
def open(model, current_idx, current_item, view, state, ctx, hook, view_reg):
    elt_view = view.element_view(view_reg, ctx, model, current_idx, current_item)
    if elt_view:
        hook.replace_view(elt_view, state)


@mark.ui_command
def parent(view, state, model, current_idx, hook, view_reg):
    elt_view = view.parent_view(view_reg, model, current_idx)
    if elt_view:
        hook.replace_view(elt_view, state)


@mark.view_factory.ui_t
def index_tree_as_list_ui_type_layout(piece, system_fn_ref):
    list_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(list_model_fn),
        ctx_params=('piece', 'ctx'),
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
