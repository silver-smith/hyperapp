import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from hyperapp.boot.htypes import TPrimitive, TOptional, tString

from . import htypes
from .services import (
    deduce_t,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.system_fn import ContextFn
from .code.model_command import model_command_ctx
from .code.list_adapter import index_list_model_state_t
from .code.tree_adapter import IndexTreeAdapterMixin, TreeAdapter

log = logging.getLogger(__name__)


class ListAsTreeAdapter(TreeAdapter, IndexTreeAdapterMixin):

    @dataclass
    class _Layer:
        open_command: Any|None = None
        item_t: Any|None = None
        model_state_t: Any|None = None
        list_fn: ContextFn|None = None

    @classmethod
    @mark.actor.ui_adapter_creg(htypes.list_as_tree_adapter.adapter)
    def from_piece(cls, piece, model, ctx, system_fn_creg, command_creg, get_model_commands, visualizer_reg):
        layers = {}
        for rec in piece.layers:
            piece_t = pyobj_creg.invite(rec.piece_t)
            layer = cls._Layer(
                open_command=command_creg.invite_opt(rec.open_children_command),
                )
            layers[piece_t] = layer
        root_item_t = pyobj_creg.invite(piece.root_item_t)
        root_layer = cls._Layer(
            open_command=command_creg.invite_opt(piece.root_open_children_command),
            item_t=root_item_t,
            model_state_t=index_list_model_state_t(root_item_t),
            list_fn=system_fn_creg.invite(piece.root_function),
            )
        return cls(system_fn_creg, command_creg, get_model_commands, visualizer_reg, model, root_item_t, ctx, root_layer, layers)

    def __init__(self, system_fn_creg, command_creg, get_model_commands, visualizer_reg, model, item_t, ctx, root_layer, layers):
        super().__init__(model, item_t)
        self._system_fn_creg = system_fn_creg
        self._command_creg = command_creg
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
        self._column_names = sorted(root_layer.item_t.fields)
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
            # TODO: Implement column inserting visual diff. Add fields to self._item_t.
            return None

    def get_item(self, id):
        if id == 0:
            return None
        parent_id = self._id_to_parent_id[id]
        item_t = self._parent_id_to_layer[parent_id].item_t
        item = self._id_to_item.get(id)
        return self._item_t(**{
            name: self._convert_field(
                name=name,
                value=getattr(item, name, None),
                t=item_t.fields.get(name),
                target_t=target_t,
                )
            for name, target_t in self._item_t.fields.items()
            })

    def _convert_field(self, name, value, t, target_t):
        if t is None:
            if isinstance(target_t, TOptional):
                return None
            if isinstance(target_t, TPrimitive):
                return target_t.type()
            raise RuntimeError(f"Can not create default value for field {name} for type {target_t}")
        if t is target_t:
            return value
        if target_t is tString:
            return str(value)
        raise RuntimeError(f"Can not convert field {name} to {target_t}: {value!r}")

    def get_item_piece(self, path):
        item_id = self.path_to_item_id(path)
        return self._id_to_piece[item_id]

    def get_item_list_model_state(self, path):
        item_id = self.path_to_item_id(path)
        parent_id = self._id_to_parent_id[item_id]
        layer = self._parent_id_to_layer[parent_id]
        item = self._id_to_item[item_id]
        return self._make_model_state(layer, item, idx=path[-1])

    def _make_model_state(self, layer, item, idx):
        return layer.model_state_t(
            current_idx=idx,
            current_item=item,
            )

    def _make_command_ctx(self, layer, ctx, model, item_id):
        item = self._id_to_item[item_id]
        parent_id = self._id_to_parent_id[item_id]
        id_list = self._id_to_children_id_list[parent_id]
        idx = id_list.index(item_id)
        model_state = self._make_model_state(layer, item, idx)
        return model_command_ctx(ctx, model, model_state)

    async def _run_open_command(self, layer, model, current_item_id):
        model_t = deduce_t(model)
        command_ctx = self._make_command_ctx(layer, self._ctx, model, current_item_id)
        unbound_command = layer.open_command
        bound_command = unbound_command.bind(command_ctx)
        piece = await bound_command.run()
        log.info("List-to-tree adapter: open command result: %s", piece)
        return piece
        
    def _load_item_list(self, layer, piece):
        kw = {
            'piece': piece,
            'model': piece,
            }
        return layer.list_fn.call(self._ctx, **kw)

    async def _load_layer(self, parent_id):
        pp_id = self._id_to_parent_id[parent_id]
        pp_layer = self._parent_id_to_layer[pp_id]
        pp_piece = self._id_to_piece[pp_id]
        log.info("List-to-tree adapter: loading layer for pp#%d parent#%d:", pp_id, parent_id)
        self._parent_id_to_layer[parent_id] = None  # Cache None if no layer is available.
        if pp_layer.open_command is None:
            log.info("List-to-tree adapter: Open command for parent#%d is not specified", parent_id)
            return None
        piece = await self._run_open_command(pp_layer, model=pp_piece, current_item_id=parent_id)
        piece_t = deduce_t(piece)
        try:
            ui_t, fn_ref = self._visualizer_reg(piece_t)
        except KeyError:
            log.info("List-to-tree adapter: Model for %s is not available", piece_t)
            return None
        if not isinstance(ui_t, htypes.model.index_list_ui_t):
            log.info("List-to-tree adapter: Model for %s is not a list", piece_t)
            return None
        try:
            layer = self._layers[piece_t]
        except KeyError:
            # Not yet included, but parent layer has open command - show it anyway.
            layer = self._Layer()
            self._layers[piece_t] = layer
        layer.item_t = pyobj_creg.invite(ui_t.item_t)
        layer.model_state_t = index_list_model_state_t(layer.item_t)
        layer.list_fn = self._system_fn_creg.invite(fn_ref)
        self._parent_id_to_layer[parent_id] = layer
        self._id_to_piece[parent_id] = piece
        item_list = self._load_item_list(layer, piece)
        log.info("List-to-tree adapter: loaded layer for parent#%d piece %r: %s", parent_id, piece, item_list)
        for item in item_list:
            self._append_item(parent_id, item)

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
