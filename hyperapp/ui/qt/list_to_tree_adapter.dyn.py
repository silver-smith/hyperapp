import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from . import htypes
from .services import (
    deduce_t,
    model_command_creg,
    pick_visualizer_info,
    pyobj_creg,
    )
from .code.tree_adapter import IndexTreeAdapterBase

log = logging.getLogger(__name__)


@dataclass
class _Layer:
    element_t: Any|None = None
    list_fn: Any|None = None
    list_fn_params: list[str]|None = None
    open_command: Any|None = None


@dataclass
class _NonRootLayer(_Layer):
    piece_t: Any = None


class ListToTreeAdapter(IndexTreeAdapterBase):

    @classmethod
    def from_piece(cls, piece, model, ctx):
        layers = {}
        for rec in piece.layers:
            piece_t = pyobj_creg.invite(rec.piece_t)
            layer = _NonRootLayer(
                piece_t=piece_t,
                open_command=rec.open_children_command,
                )
            layers[piece_t] = layer
        root_layer = _Layer(
            element_t=pyobj_creg.invite(piece.root_element_t),
            list_fn=pyobj_creg.invite(piece.root_function),
            list_fn_params=piece.root_params,
            open_command=piece.root_open_children_command,
            )
        return cls(model, ctx, root_layer, layers)

    def __init__(self, model, ctx, root_layer, layers):
        super().__init__(model, ctx)
        self._id_to_piece = {
            0: model,
            }
        self._layers = {
            **layers,
            model: root_layer,
            }
        self._column_names = sorted(root_layer.element_t.fields)
        self._parent_id_to_layer = {
            0: root_layer,
            }

    def column_count(self):
        return len(self._column_names)

    def column_title(self, column):
        return self._column_names[column]

    def cell_data(self, id, column):
        item = self._id_to_item[id]
        return getattr(item, self._column_names[column])

    def get_item_piece(self, path):
        item_id = self.path_to_item_id(path)
        return self._id_to_piece[item_id]

    async def _load_layer(self, parent_id):
        pp_id = self._id_to_parent_id[parent_id]
        pp_layer = self._parent_id_to_layer[pp_id]
        pp_piece = self._id_to_piece[pp_id]
        if pp_layer.open_command is None:
            return None
        parent_item = self._id_to_item[parent_id]
        command_ctx = self._ctx.clone_with(
            piece=pp_piece,
            current_item=parent_item,
            )
        command = model_command_creg.invite(pp_layer.open_command, command_ctx)
        piece = await command.run()
        log.info("List-to-tree adapter: open command result: %s", piece)
        piece_t = deduce_t(piece)
        try:
            ui_t, impl = pick_visualizer_info(piece_t)
        except KeyError:
            log.info("List-to-tree: Model for %s is not available", piece_t)
            return None
        if not isinstance(ui_t, htypes.ui.list_ui_t) or not isinstance(impl, htypes.ui.fn_impl):
            log.info("List-to-tree: Model for %s is not a function list", piece_t)
            return None
        try:
            layer = self._layers[piece_t]
        except KeyError:
            log.info("List-to-tree: %s is not an included piece type", piece_t)
            return
        layer.element_t = pyobj_creg.invite(ui_t.element_t)
        layer.list_fn = pyobj_creg.invite(impl.function)
        layer.list_fn_params = impl.params
        self._parent_id_to_layer[parent_id] = layer  # Cache Nones also.
        self._id_to_piece[parent_id] = piece
        log.info("List-to-tree: loaded layer for piece %r", piece)

    def _get_layer(self, parent_id):
        try:
            return self._parent_id_to_layer[parent_id]
        except KeyError:
            asyncio.create_task(self._load_layer(parent_id))
            return None

    def _retrieve_item_list(self, parent_id):
        layer = self._get_layer(parent_id)
        if not layer:
            # Not a list or unknown piece or layer is not yet loaded -> no more children (yet).
            return []
        piece = self._id_to_piece[parent_id]
        available_params = {
            **self._ctx.as_dict(),
            'piece': piece,
            'ctx': self._ctx,
            }
        kw = {
            name: available_params[name]
            for name in layer.list_fn_params
            }
        return layer.list_fn(**kw)
