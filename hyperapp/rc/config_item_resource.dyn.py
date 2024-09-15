from . import htypes
from .services import (
    mosaic,
    )
from .code.rc_resource import Resource


class ConfigItemResource(Resource):

    @classmethod
    def from_piece(cls, piece, cfg_item_creg):
        template = cfg_item_creg.invite(piece.config_item)
        return cls(piece.service_name, template)

    def __init__(self, service_name, template):
        self._service_name = service_name
        self._template = template

    @property
    def piece(self):
        return htypes.config_item_resource.config_item_resource(
            service_name=self._service_name,
            config_item=mosaic.put(self._template.piece),
            )

    @property
    def is_config_ctl_creg_item(self):
        return self._service_name == 'config_ctl_creg'

    @property
    def is_system_resource(self):
        return self._service_name == 'system'

    def configure_system(self, system):
        system.update_config(self._service_name, {self._template.key: self._template})
