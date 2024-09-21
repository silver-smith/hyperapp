from . import htypes
from .services import (
    mosaic,
    )
from .code.rc_resource import Resource


class ConfigItemResource(Resource):

    @classmethod
    def from_piece(cls, piece, cfg_item_creg):
        return cls(cfg_item_creg, piece.service_name, piece.config_item)

    def __init__(self, cfg_item_creg, service_name, template_ref):
        self._cfg_item_creg = cfg_item_creg
        self._service_name = service_name
        self._template_ref = template_ref

    @property
    def piece(self):
        return htypes.config_item_resource.config_item_resource(
            service_name=self._service_name,
            config_item=self._template_ref,
            )

    @property
    def is_config_ctl_creg_item(self):
        return self._service_name == 'config_ctl_creg'

    @property
    def is_system_resource(self):
        return self._service_name == 'system'

    def configure_system(self, system):
        template = self._cfg_item_creg.invite(self._template_ref)
        system.update_config(self._service_name, {template.key: template})
