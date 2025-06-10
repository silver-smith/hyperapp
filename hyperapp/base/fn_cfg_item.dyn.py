from . import htypes
from .services import (
    mosaic,
    web,
    )


class FnCfgItem:

    @classmethod
    def from_piece(cls, piece):
        return cls(
            system_fn=web.summon(piece.system_fn),
            )

    def __init__(self, system_fn):
        self._system_fn = system_fn

    @property
    def piece(self):
        return htypes.cfg_item.fn_cfg_item(
            system_fn=mosaic.put(self._system_fn),
            )

    def resolve(self, system, service_name):
        system_fn_creg = system.resolve_service('system_fn_creg')
        return system_fn_creg.animate(self._system_fn)
