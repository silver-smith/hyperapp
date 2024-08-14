from . import htypes
from .services import (
    mosaic,
    )
from .code.rc_resource import Resource


class ConfigItemResource(Resource):

    @classmethod
    def from_piece(cls, piece, cfg_item_creg):
        cfg_item = cfg_item_creg.invite(piece.config_item, piece.service_name)
        return cls(piece.service_name, cfg_item)

    def __init__(self, service_name, cfg_item):
        self._service_name = service_name
        self._cfg_item = cfg_item

    @property
    def piece(self):
        return htypes.config_item_resource.config_item_resource(
            service_name=self._service_name,
            config_item=mosaic.put(self._cfg_item.piece),
            )

    def configure_system(self, system):
        system.update_config('system', {self._cfg_item.key: self._cfg_item.value})
