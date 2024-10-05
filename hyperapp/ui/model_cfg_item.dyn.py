from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark


class ModelCfgItem:

    @classmethod
    @mark.actor.cfg_item_creg
    def from_piece(cls, piece):
        return cls(
            t=pyobj_creg.invite(piece.t),
            model=web.summon(piece.model),
            )

    def __init__(self, t, model):
        self._t = t
        self._model = model

    @property
    def piece(self):
        return htypes.model.cfg_item(
            t=pyobj_creg.actor_to_ref(self._t),
            model=mosaic.put(self._model),
            )

    @property
    def key(self):
        return self._t

    def resolve(self, system, service_name):
        return self._model
