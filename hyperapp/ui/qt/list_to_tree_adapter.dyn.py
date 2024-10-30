import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from . import htypes
from .services import (
    deduce_t,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.system_fn import ContextFn
from .code.tree_adapter import IndexTreeAdapterBase

log = logging.getLogger(__name__)


class ListToTreeAdapter(IndexTreeAdapterBase):

    @dataclass
    class _Layer:
        element_t: Any|None = None
        list_fn: ContextFn|None = None
        open_command_d: Any|None = None

    @classmethod
    @mark.actor.ui_adapter_creg(htypes.list_to_tree_adapter.adapter)
    def from_piece(cls, piece, model, ctx, system_fn_creg, get_model_commands, visualizer_reg):
        layers = {}
        for rec in piece.layers:
            piece_t = pyobj_creg.invite(rec.piece_t)
            layer = cls._Layer(
                open_command_d=pyobj_creg.invite_opt(rec.open_children_command_d),
                )
            layers[piece_t] = layer
        root_element_t = pyobj_creg.invite(piece.root_element_t)
        root_layer = cls._Layer(
            element_t=root_element_t,
            list_fn=system_fn_creg.invite(piece.root_function),
            open_command_d=pyobj_creg.invite_opt(piece.root_open_children_command_d),
            )
        return cls(system_fn_creg, get_model_commands, visualizer_reg, model, root_element_t, ctx, root_layer, layers)

    def __init__(self, system_fn_creg, get_model_commands, visualizer_reg, model, item_t, ctx, root_layer, layers):
        super().__init__(model, item_t)
        self._system_fn_creg = system_fn_creg
        self._get_model_commands = get_model_commands
        self._visualizer_reg = visualizer_reg
        self._ctx = ctx
        self._id_to_piece = {
            0: model,
            }
        self._layers = {
            **layers,
            deduce_t(model): root_layer,
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
        name = self._column_names[column]
        try:
            return getattr(item, name)
        except AttributeError:
            # TODO: Implement column inserting visual diff.
            return None

    def get_item_piece(self, path):
        item_id = self.path_to_item_id(path)
        return self._id_to_piece[item_id]

    async def _run_open_command(self, command_d, model, current_item):
        # TODO: Use model state instead of just current_item.
        command_ctx = self._ctx.push(
            piece=model,
            model=model,
            current_item=current_item,
            )
        command_list = self._get_model_commands(model, command_ctx)
        try:
            unbound_command = next(cmd for cmd in command_list if cmd.d == command_d)
        except StopIteration:
            raise RuntimeError(f"Command {command_d} is not available anymore")
        bound_command = unbound_command.bind(command_ctx)
        piece = await bound_command.run()
        log.info("List-to-tree adapter: open command result: %s", piece)
        return piece

    async def _load_layer(self, parent_id):
        pp_id = self._id_to_parent_id[parent_id]
        pp_layer = self._parent_id_to_layer[pp_id]
        pp_piece = self._id_to_piece[pp_id]
        self._parent_id_to_layer[parent_id] = None  # Cache None if no layer is available.
        if pp_layer.open_command_d is None:
            return None
        parent_item = self._id_to_item[parent_id]
        piece = await self._run_open_command(pp_layer.open_command_d, pp_piece, current_item=parent_item)
        piece_t = deduce_t(piece)
        try:
            ui_t, fn_ref = self._visualizer_reg(piece_t)
        except KeyError:
            log.info("List-to-tree: Model for %s is not available", piece_t)
            return None
        if not isinstance(ui_t, htypes.model.list_ui_t):
            log.info("List-to-tree: Model for %s is not a list", piece_t)
            return None
        try:
            layer = self._layers[piece_t]
        except KeyError:
            # Not yet included, but parent layer has open command - show it anyway.
            layer = self._Layer()
            self._layers[piece_t] = layer
        layer.element_t = pyobj_creg.invite(ui_t.element_t)
        layer.list_fn = self._system_fn_creg.invite(fn_ref)
        self._parent_id_to_layer[parent_id] = layer
        self._id_to_piece[parent_id] = piece
        item_list = self._load_item_list(layer, piece)
        log.info("List-to-tree: loaded layer for piece %r: %s", piece, item_list)
        for item in item_list:
            self._append_item(parent_id, item)
        
    def _load_item_list(self, layer, piece):
        kw = {
            'piece': piece,
            'model': piece,
            }
        return layer.list_fn.call(self._ctx, **kw)

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
        return self._load_item_list(layer, piece)
