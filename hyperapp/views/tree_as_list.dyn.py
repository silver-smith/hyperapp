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
            current_path=piece.current_path,
            parent_item=piece.parent_items[-1] if piece.parent_items else None,
            )
        list_ctx = ctx.clone_with(
            model=list_model,
            piece=list_model,
            )
        list_view = view_reg.invite(piece.list_view, list_ctx)
        tree_model_fn = system_fn_creg.invite(piece.tree_model_fn)
        current_path = [web.summon(elt) for elt in piece.current_path]
        parent_items = [web.summon(item) for item in piece.parent_items]
        return cls(list_view, tree_model_fn, list_model, current_path, parent_items)

    def __init__(self, list_view, tree_model_fn, list_model, current_path, parent_items):
        super().__init__(list_view)
        self._tree_model_fn = tree_model_fn
        self._list_model = list_model
        self._current_path = current_path
        self._parent_items = parent_items

    @property
    def piece(self):
        return self._piece_t(
            list_view=mosaic.put(self._base_view.piece),
            tree_model_fn=mosaic.put(self._tree_model_fn.piece),
            current_path=tuple(mosaic.put(elt) for elt in self._current_path),
            parent_items=tuple(mosaic.put(item) for item in self._parent_items),
            )

    def children_context(self, ctx):
        return ctx.clone_with(model=self._list_model)

    def primary_parent_context(self, rctx, widget):
        return rctx.clone_with(self._tree_model_state(rctx.model_state))

    @property
    def parent_key(self):
        if not self._current_path:
            return None
        return self._current_path[-1]

    def make_list_state(self, key):
        return self._base_view.make_widget_state(key)

    def element_view(self, view_reg, ctx, tree_model, current_elt, current_item):
        return self._wrapper_view(
            view_reg, ctx, tree_model,
            current_path=[*self._current_path, current_elt],
            parent_items=[*self._parent_items, current_item],
            )

    def parent_view(self, view_reg, ctx, tree_model):
        if not self._current_path:
            return None
        return self._wrapper_view(
            view_reg, ctx, tree_model,
            current_path=self._current_path[:-1],
            parent_items=self._parent_items[:-1],
            )

    def _wrapper_view(self, view_reg, ctx, tree_model, current_path, parent_items):
        list_model = htypes.tree_as_list.list_model(
            tree_model=mosaic.put(tree_model),
            tree_model_fn=mosaic.put(self._tree_model_fn.piece),
            current_path=tuple(mosaic.put(elt) for elt in current_path),
            parent_item=mosaic.put(parent_items[-1]) if parent_items else None,
            )
        list_ctx = ctx.clone_with(
            model=list_model,
            piece=list_model,
            )
        list_view = view_reg.animate(self._base_view.piece, list_ctx)
        return self.__class__(
            list_view=list_view,
            tree_model_fn=self._tree_model_fn,
            list_model=list_model,
            current_path=current_path,
            parent_items=parent_items,
            )


class IndexTreeAsListWrapperView(TreeAsListWrapperView):
    _piece_t = htypes.tree_as_list.index_view

    def _tree_model_state(self, list_state):
        return {
            'current_item': list_state.current_item,
            'current_path': [*self._current_path, list_state.current_idx],
            }


class KeyTreeAsListWrapperView(TreeAsListWrapperView):
    _piece_t = htypes.tree_as_list.key_view

    def _tree_model_state(self, list_state):
        if not list_state:
            return {
                'current_item': None,
                'current_path': None,
                }
        else:
            return {
                'current_item': list_state.current_item,
                'current_path': [*self._current_path, list_state.current_key],
                }


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
def index_open(model, current_idx, current_item, view, state, ctx, hook, view_reg):
    elt_view = view.element_view(view_reg, ctx, model, current_idx, current_item)
    if elt_view:
        hook.replace_view(elt_view, new_state=None)


@mark.ui_command
def key_open(model, current_key, current_item, view, state, ctx, hook, view_reg):
    elt_view = view.element_view(view_reg, ctx, model, current_key, current_item)
    if elt_view:
        hook.replace_view(elt_view, new_state=None)


@mark.ui_command
def parent(model, view, state, ctx, hook, view_reg):
    parent_view = view.parent_view(view_reg, ctx, model)
    new_state = parent_view.make_list_state(view.parent_key)
    if parent_view:
        hook.replace_view(parent_view, new_state)


def _list_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(list_model_fn),
        ctx_params=('piece', 'ctx'),
        service_params=('system_fn_creg',),
        )


def _ui_type_layout(system_fn_ref, list_adapter, view_t):
    list_view = htypes.list.view(
        adapter=mosaic.put(list_adapter),
        )
    return view_t(
        list_view=mosaic.put(list_view),
        tree_model_fn=system_fn_ref,
        current_path=(),
        parent_items=(),
        )


@mark.view_factory.ui_t
def index_tree_as_list_ui_type_layout(piece, system_fn_ref):
    list_adapter = htypes.list_adapter.index_fn_list_adapter(
        item_t=piece.item_t,
        system_fn=mosaic.put(_list_fn()),
        )
    return _ui_type_layout(system_fn_ref, list_adapter, htypes.tree_as_list.index_view)


@mark.view_factory.ui_t
def key_tree_as_list_ui_type_layout(piece, system_fn_ref):
    list_adapter = htypes.list_adapter.key_fn_list_adapter(
        item_t=piece.item_t,
        key_field=piece.key_field,
        key_field_t=piece.key_field_t,
        system_fn=mosaic.put(_list_fn()),
        )
    return _ui_type_layout(system_fn_ref, list_adapter, htypes.tree_as_list.key_view)
