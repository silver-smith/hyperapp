from dataclasses import dataclass
from typing import Any

from .services import (
    pyobj_creg,
    )
from .code.tree_adapter import IndexTreeAdapterBase


@dataclass
class _Layer:
    piece: Any|None=None
    element_t: Any|None = None
    fn: Any|None = None
    params: list[str]|None = None


@dataclass
class _NonRootLayer(_Layer):
    piece_t: Any = None
    command: Any = None


class ListToTreeAdapter(IndexTreeAdapterBase):

    @classmethod
    def from_piece(cls, piece, model, ctx):
        layers = {}
        for rec in piece.layers:
            piece_t = pyobj_creg.invite(rec.piece_t)
            layer = _NonRootLayer(
                piece_t=piece_t,
                command=l.open_children_command,
                )
            layers[piece_t] = layer
        root_layer = _Layer(
            piece=model,
            element_t=pyobj_creg.invite(piece.root_element_t),
            fn=pyobj_creg.invite(piece.root_function),
            params=piece.root_params,
            )
        return cls(model, ctx, root_layer, layers)

    def __init__(self, model, ctx, root_layer, layers):
        super().__init__(model, ctx)
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

    def _retrieve_item_list(self, parent_id, parent_item):
        layer = self._parent_id_to_layer[parent_id]
        available_params = {
            **self._ctx.as_dict(),
            'piece': layer.piece,
            'ctx': self._ctx,
            }
        kw = {
            name: available_params[name]
            for name in layer.params
            }
        return layer.fn(**kw)
